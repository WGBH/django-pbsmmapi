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
                links=Coalesce(
                    Cast(KT("api_data__links"), models.JSONField()),
                    models.Value({}, models.JSONField()),
                ),
                api_endpoint=KT("api_data__links__self"),
                images=Coalesce(
                    Cast(KT("api_data__data__attributes__images"), models.JSONField()),
                    models.Value([], models.JSONField()),
                ),
                hashtag=KT("api_data__data__attributes__hashtag"),
            )
        )


class ContentRecord(models.Model):
    content_id = models.UUIDField(primary_key=True)
    api_data = models.JSONField()
    last_api_status = models.PositiveIntegerField(
        _("Last API Status"),
        null=True,
        blank=True,
    )

    @classmethod
    def update_or_create(cls, content_id, last_api_status, api_data=None):
        try:
            record_instance = cls.objects.get(content_id=content_id)
            record_instance.api_data = api_data
            record_instance.last_api_status = last_api_status
            record_instance.save()
            return record_instance
        except cls.DoesNotExist:
            return cls.objects.create(
                content_id=content_id,
                api_data=api_data,
                last_api_status=last_api_status,
            )
