from http import HTTPStatus

from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import Cast
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from pbsmmapi.abstract.helpers import fix_non_aware_datetime
from pbsmmapi.api.api import get_PBSMM_record
from pbsmmapi.api.helpers import check_pagination


class GenericObjectManagement(models.Model):
    date_created = models.DateTimeField(
        _("Created On"),
        auto_now_add=True,
        help_text="Not set by API",
    )
    ingest_on_save = models.BooleanField(
        _("Ingest on Save"),
        default=False,
        help_text="If true, then will update values from the PBSMM API on save()",
    )

    class Meta:
        abstract = True


class PBSMMObjectID(models.Model):
    """
    In most parallel universes, we'd use this as the PRIMARY KEY. However,
    given the periodic necessity of having to EDIT records or manipulate them
    in the database, the issue of having to juggle 32-length random characters
    instead of a nice integer ID would be a PITA.

    So I'm being "un-pure".  Sue me.   RAD 31-Jan-2018
    """

    # TODO rename to cid
    object_id = models.UUIDField(
        _("Object ID"),
        unique=True,
        null=True,
        blank=True,  # does this work?
    )

    class Meta:
        abstract = True


class PBSMMObjectTitle(models.Model):
    """Exists for all objects"""

    title = models.CharField(_("Title"), max_length=200, null=True, blank=True)

    class Meta:
        abstract = True


class PBSMMObjectSlug(models.Model):
    """
    These exist for all objects EXCEPT Season
    (see note/whine on PBSMMObjectSortableTitle)
    """

    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=200,
    )

    class Meta:
        abstract = True


class GenericProvisional(models.Model):
    provisional = models.BooleanField(
        _("Provisional"),
        default=False,
    )

    @classmethod
    def realize(cls, data: dict):
        """
        Class method to be called from the Huey task processing ChangeLog objects
        """
        raise NotImplementedError

    class Meta:
        abstract = True


class Ingest(models.Model):
    def __init__(self, *args, **kwargs):
        self.ingest_on_save = None
        self.object_id = None
        self.slug = None
        self.last_api_status = None
        self.updated_at = None
        self.api_endpoint = None
        self.json = None
        # above fields are overridden by child classes
        super().__init__(*args, **kwargs)
        self.scraped_object_ids = []

    def process(self, endpoint, query_param=None):
        identifier = str(self.object_id or "").strip() or self.slug
        if not identifier and not self.ingest_on_save:
            return  # stop processing if we don't have clearance
        if query_param is None:
            query_param = ""
        status, json = get_PBSMM_record(f"{endpoint}{identifier}/{query_param}")
        self.last_api_status = status  # stop post_save in case of 4xx status
        if status != HTTPStatus.OK:
            return
        self.object_id = json.get("id", json["data"]["id"])
        attrs = json.get("attributes", json["data"].get("attributes"))
        for field in self._meta.get_fields():
            value = attrs.get(field.name)
            self.set_attribute(field, value)
        self.updated_at = fix_non_aware_datetime(attrs.get("updated_at"))
        self.api_endpoint = json["links"].get("self")
        self.json = json
        self.ingest_on_save = False
        return attrs

    def set_attribute(self, field, value):
        """
        Do some special processing for some fields
        """
        if value is None:
            return
        if self.is_excluded_field(field):
            return
        if self.ingest_object_flag(field):
            return
        if self.solve_datetime_field(field, value):
            return
        if self.check_for_api_id(field, value):
            return
        setattr(self, field.name, value)

    @staticmethod
    def is_excluded_field(field):
        exclude = {"AutoField", "ForeignKey"}
        return field.get_internal_type() in exclude

    def ingest_object_flag(self, field):
        """
        Ensure ingest bools are not None
        """
        if field.name.startswith("ingest_"):
            setattr(self, field.name, getattr(self, field.name) or False)
            return True

    def solve_datetime_field(self, field, value):
        if "DateTimeField" in field.get_internal_type():
            setattr(self, field.name, fix_non_aware_datetime(value))
            return True

    def check_for_api_id(self, field, value):
        """
        Sets <entity>_api_id property and retrieves name of property

        e.g. if it finds `show_api_id` will set
        self.show_api_id = json['data]['attributes]['id']
        and returns "show"
        """
        if "_api_id" not in field.name or value is None:
            return
        entity = field.name.replace("_api_id", "")
        setattr(self, field.name, value["id"])
        return entity

    def process_assets(self, endpoint, **kwargs):
        """
        Ingest Asset page by page
        kwargs: extra params send to Asset object
        """
        # prevent circular import
        from pbsmmapi.asset.models import (  # pylint: disable=import-outside-toplevel
            Asset,
        )

        def set_asset(asset: dict, status: int):
            self.scraped_object_ids.append(asset["id"])
            Asset.set(asset, last_api_status=status, **kwargs)

        self.flip_api_pages(endpoint, set_asset)

    def flip_api_pages(self, endpoint, func):
        """
        Go through every page on the api and do
        stuff for every element in data section

        For each element you must provide a callable
        receiving one element and api status
        """
        if not endpoint:
            return
        status, json = get_PBSMM_record(endpoint)
        for entity in json.get("data", []):
            func(entity, status)
        keep_going, endpoint = check_pagination(json)
        if keep_going:
            self.flip_api_pages(endpoint, func)

    def delete_stale_assets(self, **filters):
        """
        Delete leftover assets.
        > filters: params for asset queryset to identify parent object

        Returns number of objects deleted and a dictionary
        with the number of deletions per object type

        >>> self.delete_stale_assets()
        (1, {'pbsmmapi.Asset': 1})
        """
        from pbsmmapi.asset.models import (  # pylint: disable=import-outside-toplevel
            Asset,
        )

        return (
            Asset.objects.filter(**filters)
            .exclude(
                object_id__in=self.scraped_object_ids,
            )
            .delete()
        )

    class Meta:
        abstract = True


class PBSMMGenericObject(
    PBSMMObjectTitle,
    GenericObjectManagement,
):
    def last_api_status_color(self):
        """
        Colorized rendering of the last API status, used by the admin asset/
        relation tables. The status now lives on the related ContentRecord
        (``mm_content``) rather than on a local field.
        """
        status = self.mm_content.last_api_status if self.mm_content_id else None
        if status is None:
            return mark_safe('<span style="color: #999;">&mdash;</span>')
        color = "green" if int(status) == HTTPStatus.OK else "red"
        return mark_safe(f'<span style="color: {color};">{status}</span>')

    def last_updated_display(self):
        """
        Guarded rendering of the ``updated_at`` annotation (it may be NULL, and
        is only present on instances loaded through the annotating manager).
        Replaces the removed ``date_last_api_update`` field in admin tables.
        """
        updated = getattr(self, "updated_at", None)
        return updated.strftime("%x %X") if updated else "—"

    class Meta:
        abstract = True


class PBSMMGenericAsset(
    PBSMMGenericObject,
    PBSMMObjectSlug,
):
    class Meta:
        abstract = True


class PBSMMGenericShow(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericEpisode(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericSeason(
    PBSMMGenericObject,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericSpecial(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericFranchise(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    Ingest,
):
    # There is no can_embed_player field - again, laziness (see above)
    class Meta:
        abstract = True


class PBSMMBaseRecordManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                api_data=models.F("mm_content__api_data"),
                content_type=KT("api_data__data__type"),
                description_short=KT("api_data__data__attributes__description_short"),
                description_long=KT("api_data__data__attributes__description_long"),
                updated_at=Cast(
                    KT("api_data__data__attributes__updated_at"), models.DateTimeField()
                ),
                links=Cast(KT("api_data__links"), models.JSONField()),
                api_endpoint=KT("api_data__links__self"),
                images=Cast(
                    KT("api_data__data__attributes__images"), models.JSONField()
                ),
                hashtag=KT("api_data__data__attributes__hashtag"),
            )
        )
