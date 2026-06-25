from django.db import models
from django.utils.translation import gettext_lazy as _


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
