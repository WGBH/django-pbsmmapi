from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    GenericProvisional,
    PBSMMGenericSpecial,
)
from pbsmmapi.api.api import PBSMM_SPECIAL_ENDPOINT


class Special(GenericProvisional, PBSMMGenericSpecial):
    show_api_id = models.UUIDField(
        _("Show Object ID"),
        null=True,
        blank=True,  # does this work?
    )
    show = models.ForeignKey(
        "show.Show",
        related_name="specials",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    @classmethod
    def realize(cls, data: dict):
        try:
            special = cls.objects.get(
                show_api_id=data["data"]["attributes"]["show"]["id"],
                title=data["data"]["attributes"]["title"],
                provisional=True,
            )
            special.object_id = data["data"]["id"]
            special.provisional = False
            special.save()
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
        out += f"\n\t<td>{self.date_last_api_update.strftime('%x %X')}</td>"
        out += f"\n\t<td>{self.last_api_status_color()}</td>"
        out += "\n</tr>"
        return mark_safe(out)

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            self.pre_save()
            super().save(*args, **kwargs)
            self.post_save(self.id)

    def pre_save(self):
        self.process(PBSMM_SPECIAL_ENDPOINT)

    @staticmethod
    @db_task()
    def post_save(special_id):
        special = Special.objects.get(id=special_id)
        endpoint = None
        if assets := special.json["links"].get("assets"):
            endpoint = f"{assets}?platform-slug=partnerplayer"
        special.process_assets(endpoint, special_id=special_id)
        special.delete_stale_assets(special_id=special_id)

    def __str__(self):
        return f"{self.object_id} | {self.show} | {self.title} "

    class Meta:
        verbose_name = "PBS MM Special"
        verbose_name_plural = "PBS MM Specials"
        db_table = "pbsmm_special"
