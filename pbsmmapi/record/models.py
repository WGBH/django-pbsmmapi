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
    deleted = models.DateTimeField(
        _("Deleted"),
        null=True,
        blank=True,
        help_text="Set from the PBS changelog timestamp when the object was deleted upstream.",
    )
