from django.db import models
from django.utils.translation import gettext_lazy as _


class ContentRecord(models.Model):
    content_id = models.UUIDField(primary_key=True)
    api_data = models.JSONField()
    last_api_status = models.PositiveIntegerField(
        _("Last API Status"),
    )
