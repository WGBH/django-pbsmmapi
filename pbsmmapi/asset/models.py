import re
from typing import TYPE_CHECKING

from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import (
    Cast,
    Coalesce,
)
from huey.contrib.djhuey import db_task
from pycaption import detect_format
import requests

from pbsmmapi.abstract.constants import PBSMM_BASE_URL
from pbsmmapi.abstract.helpers import time_zone_aware_now
from pbsmmapi.abstract.models import (
    PBSMMBaseRecordManager,
    PBSMMGenericAsset,
)
from pbsmmapi.asset.helpers import (
    SafeTranscriptWriter,
    check_asset_availability,
)

AVAILABILITY_GROUPS = (
    ("Station Members", "station_members"),
    ("All Members", "all_members"),
    ("Public", "public"),
)

PBSMM_ASSET_ENDPOINT = f"{PBSMM_BASE_URL}api/v1/assets/"
PBSMM_LEGACY_ASSET_ENDPOINT = f"{PBSMM_ASSET_ENDPOINT}legacy/?tp_media_id="


class AssetManager(PBSMMBaseRecordManager):
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
                # TODO figure out correct format
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
    objects = AssetManager()

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

    @property
    def duration_hms(self):
        # TODO rewrite this
        """
        Show the asset's duration as #h ##m ##s.
        """
        if self.duration:
            d = self.duration
            hours = d // 3600
            if hours > 0:
                hstr = "%dh" % hours
            else:
                hstr = ""
            d %= 3600
            minutes = d // 60
            if hours > 0:
                mstr = "%02dm" % minutes
            else:
                if minutes > 0:
                    mstr = "%2dm" % minutes
                else:
                    mstr = ""
            seconds = d % 60
            if minutes > 0:
                sstr = "%02ds" % seconds
            else:
                sstr = "%ds" % seconds
            return " ".join((hstr, mstr, sstr))
        return ""

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
        # TODO rewrite this
        """
        Show the Asset's duration as ##:##:##
        """
        if self.duration:
            seconds = self.duration
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            return "%d:%02d:%02d" % (hours, minutes, seconds)
        return ""

    class Meta:
        verbose_name = "PBS MM Asset"
        verbose_name_plural = "PBS MM Assets"
        db_table = "pbsmm_asset"
        base_manager_name = "objects"

    @staticmethod
    @db_task()
    def set(asset: dict, **kwargs):
        """
        Update or creates an asset
        """
        attrs = asset["attributes"]
        links = asset.get("links", dict())

        def make_fields():
            for f in (f.name for f in Asset._meta.get_fields()):
                # temporary workaround to make Asset updates from ChangeLog ingest & get_complete_asset_data ingest work
                # until we can refactor PBSMMAPI modeling in the next sprints
                if f in ("franchise", "show", "season", "episode", "special"):
                    continue
                value = attrs.get(f)
                if value is not None:
                    yield f, value

        fields = dict(make_fields())
        fields.update(
            object_id=asset["id"],
            api_endpoint=links.get("self"),
            availability=attrs.get("availabilities"),
            asset_type=attrs.get("object_type"),
            date_last_api_update=time_zone_aware_now(),
            ingest_on_save=True,
            json=asset,
            links=links,
            **kwargs,
        )
        Asset.objects.update_or_create(
            defaults=fields,
            object_id=asset["id"],
        )[0]

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
        return f"{self.pk} | {self.mm_content.pk} ({self.legacy_tp_media_id}) | {self.title}"

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
