from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class ChangeLogEntry(models.Model):
    # TODO these fields should act as a generic FK.
    # note: MM API changelog returns data for objects without
    # endpoints (which we can't save as discrete objects),
    # as well as objects we do not currently ingest
    # ("collection" and "remoteasset"). If the `link` property
    # is always present, we could potentially use the `api_endpoint`
    # field from the abstract PBSObjectMetadata class, assuming that
    # field is being populated
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

    processed = models.BooleanField(default=False)

    @cached_property
    def action(self) -> str | None:
        return self.api_data.get("attributes", dict()).get("action", None)

    @cached_property
    def link(self) -> str | None:
        return self.api_data.get("links", dict()).get("self", None)

    def process(self):
        # TODO based on action and content type, trigger ingest or deletion of
        # our local object. Flip self.processed to True when complete.
        pass

    class Meta:
        ordering = ["timestamp"]
