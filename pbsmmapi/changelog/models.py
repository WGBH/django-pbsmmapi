from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class PBSMMObjectType(models.TextChoices):
    ASSET = "asset", _("Asset")
    EPISODE = "episode", _("Episode")
    FRANCHISE = "franchise", _("Franchise")
    SEASON = "season", _("Season")
    SHOW = "show", _("Show")
    SPECIAL = "special", _("Special")


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
        choices=PBSMMObjectType.choices,
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

    def save(self, *args, **kwargs):
        # TODO: we will need to override the save method so we do not commit to the DB entries we don't have access to
        return super().save(*args, **kwargs)

    def get_model_class(self):
        try:
            ct = ContentType.objects.get(
                app_label=self.object_type,
                model=self.object_type,
            )
            return ct.model_class()
        except ContentType.DoesNotExist:
            return None

    def create(self):
        # TODO: Model = apps.get_model(self.object_type.value, self.object_type.label) for lookup
        # TODO: will need to adjust the save methods for PBSMM object classes so post_save() is not always called
        # TODO: Asset objects are created with set, will need to be handled separately
        raise NotImplementedError

    def update(self):
        # TODO Model = apps.get_model(self.object_type.value, self.object_type.label) for lookup
        # TODO: api_data only contains the fields that are updated without the associated values, will need something similar to Ingest process() that can also work for Asset
        # TODO: the updated field for an object may sometimes be "assets", probably nothing has to be done in that case
        raise NotImplementedError

    def process(self):
        if self.action is None:
            self.processed = True
            self.save()
            return
        result = getattr(self, self.action)()
        self.processed = True
        self.save()
        return result

    class Meta:
        ordering = ["timestamp"]
