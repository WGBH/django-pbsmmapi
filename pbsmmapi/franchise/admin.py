from django.contrib import admin
from django.utils.safestring import mark_safe

from pbsmmapi.abstract.admin import PBSMMAbstractAdmin
from pbsmmapi.franchise.forms import (
    PBSMMFranchiseCreateForm,
    PBSMMFranchiseEditForm,
)
from pbsmmapi.franchise.models import Franchise


class PBSMMFranchiseAdmin(PBSMMAbstractAdmin):
    form = PBSMMFranchiseEditForm
    add_form = PBSMMFranchiseCreateForm
    model = Franchise
    list_display = (
        "pk",
        "slug",
        "object_id",
        "title_sortable",
        "date_last_api_update",
        "last_api_status_color",
    )
    list_display_links = ("pk", "slug", "object_id")
    readonly_fields = [
        "api_endpoint",
        "api_endpoint_link",
        "assemble_asset_table",
        "can_embed_player",
        "date_created",
        "date_last_api_update",
        "description_long",
        "description_short",
        "format_shows_list",
        "funder_message",
        "ga_event",
        "ga_page",
        "genre",
        "hashtag",
        "images",
        "is_excluded_from_dfp",
        "last_api_status_color",
        "links",
        "nola",
        "object_id",
        "platforms",
        "premiered_on",
        "pretty_image_list",
        "title",
        "title_sortable",
        "updated_at",
    ]
    add_readonly_fields = []
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "slug",
                    (
                        "ingest_shows",
                        "ingest_seasons",
                        "ingest_episodes",
                        "ingest_specials",
                    ),
                ),
            },
        ),
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    (
                        "title",
                        "title_sortable",
                    ),
                    (
                        "object_id",
                        "date_created",
                        "api_endpoint_link",
                    ),
                    ("date_last_api_update", "updated_at", "last_api_status_color"),
                ),
            },
        ),
        (
            "Administration",
            {
                "fields": (
                    (
                        "ingest_on_save",
                        "ingest_shows",
                        "ingest_seasons",
                        "ingest_specials",
                        "ingest_episodes",
                    ),
                ),
            },
        ),
        (
            "Shows",
            {
                "fields": ("format_shows_list",),
            },
        ),
        (
            "Assets",
            {
                "fields": ("assemble_asset_table",),
            },
        ),
        (
            "Description and Texts",
            {
                "classes": ("collapse",),
                "fields": (
                    "description_long",
                    "description_short",
                    "funder_message",
                ),
            },
        ),
        (
            "Images",
            {
                "classes": ("collapse",),
                "fields": (
                    "images",
                    "pretty_image_list",
                ),
            },
        ),
        (
            "Other",
            {
                "classes": ("collapse",),
                "fields": (
                    "hashtag",
                    ("ga_page", "ga_event"),
                    "genre",
                    "links",
                    "platforms",
                ),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.add_readonly_fields
        return super().get_readonly_fields(request, obj)

    # Switch between the fieldsets depending on whether we're adding or
    # viewing a record
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    # Apply the chosen fieldsets tuple to the viewed form
    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            kwargs.update(
                {
                    "form": self.add_form,
                    "fields": admin.utils.flatten_fieldsets(self.add_fieldsets),
                }
            )
        defaults.update(kwargs)
        return super().get_form(request, obj, **kwargs)

    def format_shows_list(self, obj):
        out = """
        <table width="100%" border=2>\n
        <tr style="background-color: #555;">
        <th colspan="3">Show</th>
        <th>API Link</th>
        <th># Assets</th>
        <th>Last Updated</th>
        <th>API Status
        </tr>
        """
        for show in obj.shows.all():
            out += show.create_table_line()

        out += "</table>"
        return mark_safe(out)

    format_shows_list.short_description = "SHOW LIST"


admin.site.register(Franchise, PBSMMFranchiseAdmin)
