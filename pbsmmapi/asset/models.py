import re

from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import (
    Cast,
    Coalesce,
)
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task
from pycaption import detect_format
import requests

from pbsmmapi.abstract.helpers import time_zone_aware_now
from pbsmmapi.abstract.models import PBSMMGenericAsset
from pbsmmapi.asset.helpers import (
    SafeTranscriptWriter,
    check_asset_availability,
)

AVAILABILITY_GROUPS = (
    ("Station Members", "station_members"),
    ("All Members", "all_members"),
    ("Public", "public"),
)

PBSMM_BASE_URL = "https://media.services.pbs.org/"
PBSMM_ASSET_ENDPOINT = f"{PBSMM_BASE_URL}api/v1/assets/"
PBSMM_LEGACY_ASSET_ENDPOINT = f"{PBSMM_ASSET_ENDPOINT}legacy/?tp_media_id="


class AssetManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                transcripts=Coalesce(
                    Cast(
                        KT("json__attributes__transcripts"),
                        models.JSONField(),
                    ),
                    models.Value([], models.JSONField()),
                ),
                captions=Coalesce(
                    Cast(
                        KT("json__attributes__captions"),
                        models.JSONField(),
                    ),
                    models.Value([], models.JSONField()),
                ),
                data_format=models.Case(
                    models.When(
                        models.Q(json__has_key="links"),
                        then=models.Value("compact"),
                    ),
                    default=models.Value("full"),
                    output_field=models.CharField(),
                ),
            )
        )


class Asset(PBSMMGenericAsset):
    objects = AssetManager()

    legacy_tp_media_id = models.BigIntegerField(
        _("COVE ID"),
        null=True,
        blank=True,
        unique=True,
        help_text="(Legacy TP Media ID)",
    )

    availability = models.JSONField(
        _("Availability"),
        default=dict,
        blank=True,
        help_text="JSON serialized Field",
    )

    duration = models.IntegerField(
        _("Duration"),
        null=True,
        blank=True,
        help_text="(in seconds)",
    )

    asset_type = models.CharField(  # This is 'clip', etc.
        _("Asset Type"),
        max_length=40,
        null=True,
        blank=True,
    )

    # CAPTIONS
    has_captions = models.BooleanField(
        _("Has Captions"),
        default=False,
    )

    tags = models.JSONField(
        _("Tags"),
        default=dict,
        blank=True,
        help_text="JSON serialized field",
    )

    # PLAYER FIELDS
    player_code = models.TextField(
        _("Player Code"),
        null=True,
        blank=True,
    )

    # Relationships

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

    # Properties and methods
    @property
    def topics(self):
        """
        Return a list of topics if the asset have it.
        According to PBS this isn't really used
            - legacy for some third parties - skipping
        However, Antiques Roadshow appears to be one of them.
        """
        try:
            return self.json.get("attributes").get("topics")
        except AttributeError:
            return []

    @property
    def content_rating(self):
        """
        What audience this asset is intended for. eg: TV-Y
        """
        try:
            return self.json.get("attributes").get("content_rating")
        except AttributeError:
            return None

    @property
    def content_rating_description(self):
        """
        Verbose description of the content rating. eg: General Audience
        """
        try:
            return self.json.get("attributes").get("content_rating_description")
        except AttributeError:
            return None

    def asset_publicly_available(self):
        """
        This is mostly for tables listing Assets in the Admin detail page for
        ancestral objects: e.g., an Episode's page in the Admin has a list of
        the episode's assets, and this provides a simple column to show
        availability in that list.
        """
        if self.availability:
            public_window = self.availability.get("public", None)
            if public_window:
                return check_asset_availability(
                    start=public_window["start"],
                    end=public_window["end"],
                )[0]
        return None

    asset_publicly_available.short_description = "Pub. Avail."
    asset_publicly_available.boolean = True

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
        return (
            f"{self.pk} | {self.object_id} ({self.legacy_tp_media_id}) | {self.title}"
        )
