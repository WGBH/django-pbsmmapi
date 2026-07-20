import re
from typing import TYPE_CHECKING
from uuid import UUID

from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import (
    Cast,
    Coalesce,
)
from pycaption import detect_format
import requests

from pbsmmapi.abstract.models import PBSMMGenericAsset
from pbsmmapi.api.api import PBSMM_ASSET_ENDPOINT
from pbsmmapi.asset.helpers import (
    SafeTranscriptWriter,
    check_asset_availability,
)
from pbsmmapi.record.models import PBSMMBaseRecordManager

AVAILABILITY_GROUPS = (
    ("Station Members", "station_members"),
    ("All Members", "all_members"),
    ("Public", "public"),
)


class PBSMMAssetManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                asset_type=KT("api_data__data__attributes__object_type"),
                premiered_on=Cast(
                    KT("api_data__data__attributes__premiered_on"),
                    models.DateField(),
                ),
                encored_on=Cast(
                    KT("api_data__data__attributes__encored_on"), models.DateTimeField()
                ),
                is_excluded_from_dfp=Cast(
                    KT("api_data__data__attributes__is_excluded_from_dfp"),
                    models.BooleanField(),
                ),
                duration=Cast(
                    KT("api_data__data__attributes__duration"), models.IntegerField()
                ),
                content_rating=KT("api_data__data__attributes__content_rating"),
                content_rating_description=KT(
                    "api_data__data__attributes__content_rating_description"
                ),
                language=KT("api_data__data__attributes__language"),
                geo_profile=KT("api_data__data__attributes__geo_profile"),
                can_embed_player=KT("api_data__data__attributes__can_embed_player"),
                legacy_tp_media_id=KT("api_data__data__attributes__legacy_tp_media_id"),
                tags=Cast(KT("api_data__data__attributes__tags"), models.JSONField()),
                platforms=Cast(
                    KT("api_data__data__attributes__platforms"), models.JSONField()
                ),
                player_code=Cast(
                    KT("api_data__data__attributes__player_code"), models.TextField()
                ),
                availability=Cast(
                    KT("api_data__data__attributes__availabilities"), models.JSONField()
                ),
                parent_tree=Cast(
                    KT("api_data__data__attributes__parent_tree"), models.JSONField()
                ),
                has_captions=Cast(
                    KT("api_data__data__attributes__has_captions"),
                    models.BooleanField(),
                ),
                transcripts=Coalesce(
                    Cast(
                        KT("api_data__data__attributes__transcripts"),
                        models.JSONField(),
                    ),
                    models.Value([], models.JSONField()),
                ),
                captions=Coalesce(
                    Cast(
                        KT("api_data__data__attributes__captions"),
                        models.JSONField(),
                    ),
                    models.Value([], models.JSONField()),
                ),
                topics=Coalesce(
                    Cast(
                        KT("api_data__data__attributes__topics"),
                        models.JSONField(),
                    ),
                    models.Value([], models.JSONField()),
                ),
                data_format=models.Case(
                    models.When(
                        models.Q(api_data__data__attributes__has_key="captions"),
                        then=models.Value("full"),
                    ),
                    default=models.Value("compact"),
                    output_field=models.CharField(),
                ),
            )
        )


class Asset(PBSMMGenericAsset):
    objects = PBSMMAssetManager()

    # Relationships
    mm_content = models.OneToOneField(
        "record.ContentRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    episode = models.ForeignKey(
        "episode.Episode",
        null=True,
        blank=True,
        related_name="assets",
        on_delete=models.SET_NULL,
    )

    season = models.ForeignKey(
        "season.Season",
        null=True,
        blank=True,
        related_name="assets",
        on_delete=models.SET_NULL,
    )

    show = models.ForeignKey(
        "show.Show",
        null=True,
        blank=True,
        related_name="assets",
        on_delete=models.SET_NULL,
    )

    special = models.ForeignKey(
        "special.Special",
        null=True,
        blank=True,
        related_name="assets",
        on_delete=models.SET_NULL,
    )

    franchise = models.ForeignKey(
        "franchise.Franchise",
        null=True,
        blank=True,
        related_name="assets",
        on_delete=models.SET_NULL,
    )

    def asset_publicly_available(self):
        """
        Is the asset currently inside its public availability window? Reads the
        ``availability`` annotation. Used by both the admin (wrapped with a
        boolean display) and the asset relation tables.
        """
        if self.availability:
            public_window = self.availability.get("public", None)
            if public_window:
                return check_asset_availability(
                    start=public_window["start"],
                    end=public_window["end"],
                )[0]
        return None

    @property
    def formatted_duration(self):
        """
        Show the Asset's duration as ##:##:##
        """
        if self.duration:
            hours, remainder = divmod(self.duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return ""

    class Meta:
        verbose_name = "PBS MM Asset"
        verbose_name_plural = "PBS MM Assets"
        db_table = "pbsmm_asset"
        base_manager_name = "objects"

    @property
    def query_param(self):
        return "?platform-slug=partnerplayer"

    @property
    def endpoint(self):
        return PBSMM_ASSET_ENDPOINT

    def set_parent(self):
        parental_fields = ["episode", "season", "show", "special", "franchise"]
        target_values: dict = {field: None for field in parental_fields}

        # Reload the related ContentRecord to ensure we have the latest api_data
        # (e.g. if it was updated in the database during pre_save).
        if self.mm_content:
            try:
                self.mm_content.refresh_from_db()
            except Exception:
                pass

        try:
            parent_tree = self.mm_content.api_data["data"]["attributes"]["parent_tree"]
            if parent_tree:
                parent_type: str = parent_tree.get("type")
                parent_cid: str = parent_tree.get("id")
                if parent_type in parental_fields and parent_cid:
                    try:
                        model_class = self._meta.get_field(parent_type).related_model
                        assert model_class is not None
                        parent_obj = model_class.objects.filter(
                            mm_content_id=parent_cid
                        ).first()
                        if parent_obj:
                            target_values[parent_type] = parent_obj
                    except LookupError:
                        pass
        except (KeyError, TypeError):
            pass

        # Apply target values to ensure single correct parent is populated
        for field, value in target_values.items():
            setattr(self, field, value)

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False) or self.deleted is not None
        content_id = kwargs.pop("content_id", None)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            self.pre_save(content_id)
            self.set_parent()
            super().save(*args, **kwargs)

    @property
    def transcript_url(self) -> str | None:
        return next(
            filter(lambda x: x.get("primary"), self.transcripts),
            dict(),
        ).get("url", None)

    @property
    def caption_url(self) -> str | None:
        """
        We only need one caption file for the purpose of converting to
        a transcript (as a fallback when no transcript is in the Asset data).
        The list of profiles below is ranked by compatability (plus a little
        personal preference).
        """
        caption_map = {config["profile"]: config["url"] for config in self.captions}
        profiles = [
            "WebVTT",
            "SRT",
            "Caption-SAMI",
            "DFXP",
        ]
        for profile in profiles:
            url = caption_map.get(profile, None)
            if url:
                return url

    def fetch_transcript(self) -> str | None:
        if self.transcript_url:
            r = requests.get(self.transcript_url)
            r.encoding = "UTF-8"
            return r.text

        if self.caption_url:
            r = requests.get(self.caption_url)
            r.encoding = "UTF-8"
            captions = r.text
            reader = detect_format(captions)
            return SafeTranscriptWriter().write(reader().read(captions))

    def get_video_id_from_player_code(self):
        regex = r"org\/partnerplayer\/(.*)((?:\/\?))"
        part_of_player_code = re.search(regex, self.player_code)
        return part_of_player_code.group(1)

    def __str__(self):
        return f"{self.pk} | {self.mm_content_id} ({self.legacy_tp_media_id}) | {self.title}"

    if TYPE_CHECKING:
        api_data: dict
        duration: int
        transcripts: list[dict]
        captions: list[dict]
        player_code: str
        data_format: str
        is_excluded_from_dfp: bool
        platforms: list[dict]
        availability: dict
        legacy_tp_media_id: int
        mm_content_id: UUID
