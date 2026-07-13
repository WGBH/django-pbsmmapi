from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import (
    Cast,
    Coalesce,
)
from django.utils.translation import gettext_lazy as _


class PBSMMBaseRecordManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(api_data=models.F("mm_content__api_data"))
            .annotate(
                content_id=models.F("mm_content__content_id"),
                content_type=KT("api_data__data__type"),
                description_short=KT("api_data__data__attributes__description_short"),
                description_long=KT("api_data__data__attributes__description_long"),
                updated_at=Cast(
                    KT("api_data__data__attributes__updated_at"), models.DateTimeField()
                ),
                api_links=Coalesce(
                    Cast(KT("api_data__links"), models.JSONField()),
                    models.Value({}, models.JSONField()),
                ),
                api_endpoint=KT("api_data__links__self"),
                images=Coalesce(
                    Cast(KT("api_data__data__attributes__images"), models.JSONField()),
                    models.Value([], models.JSONField()),
                ),
                hashtag=KT("api_data__data__attributes__hashtag"),
                date_last_api_update=models.F("mm_content__date_last_api_update"),
            )
        )


class ContentRecord(models.Model):
    content_id = models.UUIDField(primary_key=True)
    api_data = models.JSONField(default=dict)
    last_api_status = models.PositiveIntegerField(
        _("Last API Status"),
        null=True,
        blank=True,
    )
    date_last_api_update = models.DateTimeField(
        _("Last API Retrieval"),
        help_text="Not set by API",
        null=True,
        blank=True,
    )
    deleted = models.DateTimeField(
        _("Deleted"),
        null=True,
        blank=True,
        db_index=True,
        help_text="Set from the PBS changelog timestamp when the object was deleted upstream.",
    )
