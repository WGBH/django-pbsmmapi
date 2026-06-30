from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import Cast
from django.utils.safestring import mark_safe
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    GenericProvisional,
    PBSMMGenericSpecial,
)
from pbsmmapi.api.api import PBSMM_SPECIAL_ENDPOINT
from pbsmmapi.record.models import (
    ContentRecord,
    PBSMMBaseRecordManager,
)


class PBSMMSpecialManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                nola=KT("api_data__data__attributes__nola"),
                language=KT("api_data__data__attributes__language"),
                tms_id=KT("api_data__data__attributes__tms_id"),
                internal_links=Cast(
                    KT("api_data__data__attributes__links"), models.JSONField()
                ),
                premiered_on=Cast(
                    KT("api_data__data__attributes__premiered_on"),
                    models.DateField(),
                ),
                encored_on=Cast(
                    KT("api_data__data__attributes__encored_on"),
                    models.DateField(),
                ),
                show_content_id=Cast(
                    KT("api_data__data__attributes__show__id"), models.UUIDField()
                ),
            )
        )


class Special(GenericProvisional, PBSMMGenericSpecial):
    objects = PBSMMSpecialManager()
    Record = ContentRecord

    show = models.ForeignKey(
        "show.Show",
        related_name="specials",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    mm_content = models.OneToOneField(
        "record.ContentRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @classmethod
    def realize(cls, data: dict, skip_ingest: bool = False):
        try:
            special = cls.objects.get(
                show_api_id=data["data"]["attributes"]["show"]["id"],
                title=data["data"]["attributes"]["title"],
                provisional=True,
            )
            special.object_id = data["data"]["id"]
            special.provisional = False
            special.save(skip_ingest=skip_ingest)
        except cls.DoesNotExist:
            return

    @property
    def nola_code(self):
        if self.nola is None or self.nola == "":
            return None
        if self.show.nola is None or self.show.nola == "":
            return None
        return f"{self.show.nola}-{self.nola}"

    def create_table_line(self):
        out = "<tr>"
        out += f'\n\t<td><a href="/admin/special/pbsmmspecial/{self.id}'
        out += f'/change/"><B>{self.title}</b></a></td>'
        out += f'\n\t<td><a href="{self.api_endpoint}" target="_new">API</a></td>'
        out += f"\n\t<td>{self.assets.count()}</td>"
        out += f"\n\t<td>{self.last_updated_display()}</td>"
        out += f"\n\t<td>{self.last_api_status_color()}</td>"
        out += "\n</tr>"
        return mark_safe(out)

    @property
    def query_param(self):
        return None

    @property
    def endpoint(self):
        return PBSMM_SPECIAL_ENDPOINT

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False)
        content_id = kwargs.pop("content_id", None)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            self.pre_save(content_id)
            super().save(*args, **kwargs)
            self.post_save(self.id)

    @classmethod
    @db_task()
    def post_save(cls, special_id):
        special = cls.objects.get(id=special_id)
        endpoint = None
        if assets := special.links.get("assets"):
            endpoint = f"{assets}?platform-slug=partnerplayer"
        special.process_assets(endpoint, special_id=special_id)
        special.delete_stale_assets(special_id=special_id)

    def __str__(self):
        return f"{self.content_id} | {self.show} | {self.title} "

    class Meta:
        verbose_name = "PBS MM Special"
        verbose_name_plural = "PBS MM Specials"
        db_table = "pbsmm_special"
