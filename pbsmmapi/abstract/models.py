from http import HTTPStatus

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

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
    Record = None

    def __init__(self, *args, **kwargs):
        self.ingest_on_save = None
        self.content_id = None
        self.slug = None
        # above fields are overridden by child classes
        super().__init__(*args, **kwargs)
        self.scraped_object_ids = []

    @property
    def query_param(self):
        raise NotImplementedError

    @property
    def endpoint(self):
        raise NotImplementedError

    def process(self, query_param=None, content_id=None):
        identifier = str(content_id or self.content_id or "").strip() or self.slug
        query_param = query_param or self.query_param
        if not identifier and not self.ingest_on_save:
            return  # stop processing if we don't have clearance
        if query_param is None:
            query_param = ""
        status, json_data = get_PBSMM_record(
            f"{self.endpoint}{identifier}/{query_param}"
        )
        self.ingest_on_save = False
        return status, json_data

    def _pre_save_update_fields(self, json_data, content):
        self.title = json_data["data"]["attributes"]["title"]
        self.slug = json_data["data"]["attributes"]["slug"]
        self.mm_content = content

    def pre_save(self, content_id=None):
        status, json_data = self.process(
            content_id=content_id,
        )
        if status != HTTPStatus.OK:
            if self.mm_content is not None:
                self.mm_content.last_api_status = status
                self.mm_content.save()
            return status

        content_id = json_data["data"]["id"]
        content = self.Record.update_or_create(
            content_id=content_id,
            last_api_status=status,
            api_data=json_data,
        )
        if self.mm_content is None:
            self._pre_save_update_fields(json_data, content)

        return status

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

    class Meta:
        abstract = True


class IngestWithAssets(Ingest):
    def process_assets(self, endpoint, **kwargs):
        """
        Ingest Asset page by page
        kwargs: extra params send to Asset object
        """
        # prevent circular import
        from pbsmmapi.asset.models import (  # pylint: disable=import-outside-toplevel
            Asset,
        )

        def set_asset(mm_asset_data: dict, _):
            self.scraped_object_ids.append(mm_asset_data["id"])
            try:
                asset = Asset.objects.get(content_id=mm_asset_data["id"])
                asset.save()
            except Asset.DoesNotExist:
                asset = Asset(**kwargs)
                asset.ingest_on_save = True
                asset.save(content_id=mm_asset_data["id"])

        self.flip_api_pages(endpoint, set_asset)

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
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericShow(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    IngestWithAssets,
):
    class Meta:
        abstract = True


class PBSMMGenericEpisode(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    IngestWithAssets,
):
    class Meta:
        abstract = True


class PBSMMGenericSeason(
    PBSMMGenericObject,
    IngestWithAssets,
):
    class Meta:
        abstract = True


class PBSMMGenericSpecial(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    IngestWithAssets,
):
    class Meta:
        abstract = True


class PBSMMGenericFranchise(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    IngestWithAssets,
):
    class Meta:
        abstract = True
