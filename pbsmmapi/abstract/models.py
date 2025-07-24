from http import HTTPStatus

from django.db import models
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
    date_last_api_update = models.DateTimeField(
        _("Last API Retrieval"),
        help_text="Not set by API",
        auto_now=True,
        null=True,
    )
    ingest_on_save = models.BooleanField(
        _("Ingest on Save"),
        default=False,
        help_text="If true, then will update values from the PBSMM API on save()",
    )
    last_api_status = models.PositiveIntegerField(
        _("Last API Status"),
        null=True,
        blank=True,
    )
    json = models.JSONField(
        _("JSON"),
        default=dict,
        blank=True,
        help_text="This is the last JSON uploaded.",
    )

    def last_api_status_color(self):
        template = '<b><span style="color:#%s;">%d</span></b>'
        if self.last_api_status:
            if self.last_api_status == 200:
                return mark_safe(template % ("0c0", self.last_api_status))
            return mark_safe(template % ("f00", self.last_api_status))
        return mark_safe(self.last_api_status)

    last_api_status_color.short_description = "Status"

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


class PBSObjectMetadata(models.Model):
    """Exists for all objects"""

    api_endpoint = models.URLField(
        _("Link to API Record"),
        null=True,
        blank=True,
        help_text="Endpoint to original record from the API",
    )

    def api_endpoint_link(self):
        # This just makes the field clickable in the Admin (why cut and paste
        # when you can click?)
        return mark_safe(
            f'<a href="{self.api_endpoint}" target="_new">{self.api_endpoint}</a>'
        )

    api_endpoint_link.short_description = "Link to API"

    class Meta:
        abstract = True


class PBSMMObjectTitle(models.Model):
    """Exists for all objects"""

    title = models.CharField(_("Title"), max_length=200, null=True, blank=True)

    class Meta:
        abstract = True


class PBSMMObjectSortableTitle(models.Model):
    """
    Exists for all objects EXCEPT Collection - so we have to separate it
    (I don't understand why the API just didn't create this across records...)
    """

    title_sortable = models.CharField(
        _("Sortable Title"), max_length=200, null=True, blank=True
    )

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


class PBSMMObjectTitleSortableTitle(PBSMMObjectTitle, PBSMMObjectSortableTitle):
    """Lump them together"""

    class Meta:
        abstract = True


class PBSMMObjectDescription(models.Model):
    """These exist for all Objects"""

    description_long = models.TextField(_("Long Description"))
    description_short = models.TextField(_("Short Description"))

    class Meta:
        abstract = True


class PBSMMObjectDates(models.Model):
    """This exists for all objects"""

    updated_at = models.DateTimeField(
        _("Updated At"),
        null=True,
        blank=True,
        help_text="API record modified date",
    )

    class Meta:
        abstract = True


class PBSMMBroadcastDates(models.Model):
    """
    premiered_on exists for Episode, Franchise, Show, and Special but NOT
    Collection or Season

    encored_on ONLY exists for Episode so we might have to
    split them up
    """

    premiered_on = models.DateTimeField(_("Premiered On"), null=True, blank=True)

    @property
    def short_premiere_date(self):
        return self.premiered_on.strftime("%x")

    class Meta:
        abstract = True


class PBSMMNOLA(models.Model):
    """
    This exists for Episode, Franchise, and Special but NOT for Collection,
    Show, or Season
    """

    nola = models.CharField(
        _("NOLA Code"),
        max_length=8,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PBSMMImage(models.Model):
    images = models.JSONField(
        _("Images"),
        default=dict,
        blank=True,
        help_text="JSON serialized field",
    )

    def pretty_image_list(self):
        if self.images:
            image_list = self.images
            out = '<table width="100%">'
            out += "<tr><th>Profile</th><th>Updated At</th></tr>"
            for image in image_list:
                out += "\n<tr>"
                out += f'<td><a href="{image["image"]}" target="_new">'
                out += f"{image['profile']}</a></td>"
                out += f"<td>{image['updated_at']}</td>"
                out += "</tr>"
            out += "</table>"
            return mark_safe(out)
        return None

    pretty_image_list.short_description = "Image List"

    class Meta:
        abstract = True


class PBSMMFunder(models.Model):
    funder_message = models.TextField(
        _("Funder Message"),
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PBSMMPlayerMetadata(models.Model):
    is_excluded_from_dfp = models.BooleanField(
        _("Is excluded from DFP"),
        default=False,
    )

    can_embed_player = models.BooleanField(
        _("Can Embed Player"),
        default=False,
    )

    class Meta:
        abstract = True


class PBSMMLinks(models.Model):
    links = models.JSONField(
        _("Links"),
        default=dict,
        blank=True,
        help_text="JSON serialized field",
    )

    class Meta:
        abstract = True


class PBSMMPlatforms(models.Model):
    platforms = models.JSONField(
        _("Platforms"),
        default=dict,
        blank=True,
        help_text="JSON serialized field",
    )

    class Meta:
        abstract = True


class PBSMMGeo(models.Model):
    # countries --- hold off until needed
    geo_profile = models.JSONField(
        _("Geo Profile"),
        default=dict,
        blank=True,
        help_text="JSON serialized field",
    )

    class Meta:
        abstract = True


class PBSMMGoogleTracking(models.Model):
    ga_page = models.CharField(
        _("GA Page Tag"),
        max_length=40,
        null=True,
        blank=True,
    )
    ga_event = models.CharField(
        _("GA Event Tag"),
        max_length=40,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PBSMMGenre(models.Model):
    genre = models.JSONField(
        _("Genre"),
        default=dict,
        blank=True,
        help_text="JSON Serialized Field",
    )

    class Meta:
        abstract = True


class PBSMMLanguage(models.Model):
    language = models.CharField(
        _("Language"),
        max_length=10,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PBSMMAudience(models.Model):
    audience = models.JSONField(
        _("Audience"),
        default=dict,
        blank=True,
        help_text="JSON Serialized Field",
    )

    class Meta:
        abstract = True


class PBSMMHashtag(models.Model):
    hashtag = models.CharField(
        _("Hashtag"),
        max_length=100,
        null=True,
        blank=True,
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
    PBSMMObjectID,
    PBSMMObjectTitleSortableTitle,
    PBSMMObjectDescription,
    PBSMMObjectDates,
    GenericObjectManagement,
    PBSObjectMetadata,
):
    class Meta:
        abstract = True


class PBSMMGenericAsset(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    PBSMMImage,
    PBSMMFunder,
    PBSMMPlayerMetadata,
    PBSMMLinks,
    PBSMMGeo,
    PBSMMPlatforms,
    PBSMMLanguage,
):
    class Meta:
        abstract = True


class PBSMMGenericRemoteAsset(PBSMMGenericObject):
    class Meta:
        abstract = True


class PBSMMGenericShow(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    PBSMMLinks,
    PBSMMNOLA,
    PBSMMHashtag,
    PBSMMImage,
    PBSMMGenre,
    PBSMMFunder,
    PBSMMPlayerMetadata,
    PBSMMGoogleTracking,
    PBSMMPlatforms,
    PBSMMAudience,
    PBSMMBroadcastDates,
    PBSMMLanguage,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericEpisode(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    PBSMMFunder,
    PBSMMLanguage,
    PBSMMBroadcastDates,
    PBSMMNOLA,
    PBSMMLinks,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericSeason(
    PBSMMGenericObject,
    PBSMMLinks,
    PBSMMImage,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericSpecial(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    PBSMMLanguage,
    PBSMMBroadcastDates,
    PBSMMNOLA,
    PBSMMLinks,
    Ingest,
):
    class Meta:
        abstract = True


class PBSMMGenericCollection(PBSMMGenericObject, PBSMMObjectSlug, PBSMMImage):
    # There is no sortable title field - it is allowed in the model purely out
    # of laziness since abstracting it out from PBSMMGenericObject would be
    # more-complicated than leaving it in. PLUS I suspect that eventually it'll
    # be added...
    class Meta:
        abstract = True


class PBSMMGenericFranchise(
    PBSMMGenericObject,
    PBSMMObjectSlug,
    PBSMMFunder,
    PBSMMNOLA,
    PBSMMBroadcastDates,
    PBSMMImage,
    PBSMMPlatforms,
    PBSMMLinks,
    PBSMMHashtag,
    PBSMMGoogleTracking,
    PBSMMGenre,
    PBSMMPlayerMetadata,
    Ingest,
):
    # There is no can_embed_player field - again, laziness (see above)
    class Meta:
        abstract = True
