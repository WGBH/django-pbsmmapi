from django.db import models
from django.utils.translation import gettext_lazy as _


class ChangeLogEntry(models.Model):
    object_type = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    content_id = models.UUIDField(
        _("Object ID"),
        null=True,
    )

    timestamp = models.DateTimeField()
    api_data = models.JSONField(null=True)

    class Meta:
        ordering = ["timestamp"]
