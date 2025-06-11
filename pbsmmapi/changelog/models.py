from django.db import models
from django.utils.translation import gettext_lazy as _

DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
TO_DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class PBSMMResourceType(models.TextChoices):
    ASSET = "asset", _("Asset")
    EPISODE = "episode", _("Episode")
    FRANCHISE = "franchise", _("Franchise")
    SEASON = "season", _("Season")
    SHOW = "show", _("Show")
    SPECIAL = "special", _("Special")


class ChangeLog(models.Model):
    # Let's try one instance per resource type/CID
    resource_type = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        choices=PBSMMResourceType.choices,
    )
    content_id = models.UUIDField(
        _("Content ID"),
        null=True,
        unique=True,
    )

    # dict where keys are timestamps and values are the remaining
    # changelog entry attributes (action and updated_fields)
    entries = models.JSONField(default=dict)
    # to pick up ingest where we left off
    latest_timestamp = models.DateTimeField(null=True)

    processed = models.BooleanField(default=False)
    # Not ideal - we should create URL from resource type/content ID
    api_url = models.URLField(null=True)
    api_status = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        self.latest_timestamp = max(self.entries.keys(), default=None)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["latest_timestamp"]
