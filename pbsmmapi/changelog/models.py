from datetime import (
    UTC,
    datetime,
)
from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields.json import KT
from django.utils.translation import gettext_lazy as _

from pbsmmapi.abstract.constants import PBSMM_BASE_URL
from pbsmmapi.record.models import PBSMMBaseRecordManager


def parse_changelog_timestamp(timestamp: str) -> datetime:
    """Parse a changelog ISO timestamp string into an aware UTC datetime.

    Any offset in the string is normalized to UTC; a timestamp with no
    timezone is assumed to be UTC (not the local zone).
    """
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class PBSMMResourceType(models.TextChoices):
    ASSET = "asset", _("Asset")
    EPISODE = "episode", _("Episode")
    FRANCHISE = "franchise", _("Franchise")
    SEASON = "season", _("Season")
    SHOW = "show", _("Show")
    SPECIAL = "special", _("Special")


class ChangeLog(models.Model):
    objects = PBSMMBaseRecordManager()

    resource_type = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        choices=PBSMMResourceType,
    )

    # dict where keys are timestamps and values are the remaining
    # changelog entry attributes (action and updated_fields)
    entries = models.JSONField(default=dict)
    # to pick up ingest where we left off
    latest_timestamp = models.DateTimeField(null=True)

    ingested = models.BooleanField(default=False)

    api_crawled = models.DateTimeField(null=True)
    mm_content = models.OneToOneField(
        "record.ContentRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @property
    def api_url(self):
        return f"{PBSMM_BASE_URL}api/v1/{self.resource_type}s/{self.content_id}/"

    def save(self, *args, **kwargs):
        # compare by parsed instant, not string order, so entries with
        # differing formats (e.g. missing microseconds) still pick the
        # chronologically latest timestamp; store the parsed datetime (not the
        # raw string key) so the in-memory value matches the DateTimeField.
        latest = max(
            self.entries.keys(),
            default=None,
            key=parse_changelog_timestamp,
        )
        self.latest_timestamp = (
            parse_changelog_timestamp(latest) if latest is not None else None
        )
        if self.get_instance() is not None:
            self.ingested = True
        super().save(*args, **kwargs)

    def get_content_type(self):
        return ContentType.objects.get(
            app_label=self.resource_type,
            model=self.resource_type,
        )

    def get_model_class(self):
        try:
            ct = ContentType.objects.get(
                app_label=self.resource_type,
                model=self.resource_type,
            )
            return ct.model_class()
        except ContentType.DoesNotExist:
            return None

    def get_instance(self):
        # try to get a previously saved instance
        model = self.get_model_class()
        assert model is not None
        assert self.mm_content is not None
        try:
            return model.objects.get(content_id=self.mm_content.content_id)
        except model.DoesNotExist:
            return None

    def __str__(self):
        return f"Changelog for {self.resource_type} {self.mm_content.content_id}"

    class Meta:
        verbose_name = "PBS MM Changelog"
        verbose_name_plural = "PBS MM Changelogs"
        db_table = "pbsmm_changelog"
        ordering = ["latest_timestamp"]

    if TYPE_CHECKING:
        content_id: str


class ShowChangeLogManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(resource_type="show")
            .annotate(
                franchise_content_id=KT("api_data__data__attributes__franchise__id")
            )
            .annotate(title=KT("api_data__data__attributes__title"))
        )


class ShowChangeLog(ChangeLog):
    objects = ShowChangeLogManager()

    class Meta:
        proxy = True


class SeasonChangeLogManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(resource_type="season")
            .annotate(show_content_id=KT("api_data__data__attributes__show__id"))
            .annotate(ordinal=KT("api_data__data__attributes__ordinal"))
        )


class SeasonChangeLog(ChangeLog):
    objects = SeasonChangeLogManager()

    class Meta:
        proxy = True


class EpisodeChangeLogManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(resource_type="episode")
            .annotate(show_content_id=KT("api_data__data__attributes__show__id"))
            .annotate(season_content_id=KT("api_data__data__attributes__season__id"))
            .annotate(ordinal=KT("api_data__data__attributes__ordinal"))
        )


class EpisodeChangeLog(ChangeLog):
    objects = EpisodeChangeLogManager()

    class Meta:
        proxy = True


class SpecialChangeLogManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(resource_type="special")
            .annotate(show_content_id=KT("api_data__data__attributes__show__id"))
            .annotate(title=KT("api_data__data__attributes__title"))
        )


class SpecialChangeLog(ChangeLog):
    objects = SpecialChangeLogManager()

    class Meta:
        proxy = True


class AssetChangeLogManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(resource_type="asset")
            .annotate(
                parent_type=KT("api_data__data__attributes__parent_tree__type"),
                parent_id=KT("api_data__data__attributes__parent_tree__id"),
            )
        )


class AssetChangeLog(ChangeLog):
    objects = AssetChangeLogManager()

    def get_parent_model_class(self):
        try:
            ct = ContentType.objects.get(
                app_label=self.parent_type,
                model=self.parent_type,
            )
            return ct.model_class()
        except ContentType.DoesNotExist:
            return None

    def get_parent_instance(self):
        # try to get a previously saved instance
        model = self.get_parent_model_class()
        assert model is not None
        try:
            return model.objects.get(content_id=self.parent_id)
        except model.DoesNotExist:
            return None

    def __str__(self):
        return f"AssetChangelog for {self.content_id} - parent {self.get_parent_instance()}"

    class Meta:
        proxy = True

    if TYPE_CHECKING:
        parent_type: str
        parent_id: str
