from django.contrib import admin
from django.utils.safestring import mark_safe

from pbsmmapi.abstract.admin import PBSMMAbstractAdmin
from pbsmmapi.season.forms import (
    PBSMMSeasonCreateForm,
    PBSMMSeasonEditForm,
)
from pbsmmapi.season.models import Season


class PBSMMSeasonAdmin(PBSMMAbstractAdmin):
    form = PBSMMSeasonEditForm
    add_form = PBSMMSeasonCreateForm
    model = Season
    list_display = (
        "pk",
        "printable_title",
        "show",
        "ordinal",
        "date_last_api_update",
        "last_api_status_color",
    )
    list_display_links = ("pk", "printable_title")
    list_filter = ("show__title_sortable",)
    # Why so many readonly_fields?  Because we don't want to override what's
    # coming from the API, but we do want to be able to view it in the context
    # of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        "api_endpoint",
        "api_endpoint_link",
        "assemble_asset_table",
        "date_created",
        "date_last_api_update",
        "description_long",
        "description_short",
        "format_episode_list",
        "images",
        "last_api_status",
        "last_api_status_color",
        "links",
        "ordinal",
        "pretty_image_list",
        "show_api_id",
        "title",
        "title_sortable",
        "updated_at",
    ]

    add_fieldsets = (
        (
            None,
            {
                "fields": ("object_id", "show", "ingest_episodes"),
            },
        ),
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("ingest_on_save", "ingest_episodes"),
                    (
                        "date_created",
                        "date_last_api_update",
                        "updated_at",
                        "last_api_status",
                        "last_api_status_color",
                    ),
                    "api_endpoint_link",
                ),
            },
        ),
        (
            "Episodes",
            {"fields": ("format_episode_list",)},
        ),
        (
            "Season Metadata",
            {"fields": ("ordinal", "show_api_id")},
        ),
        (
            "Assets",
            {"fields": ("assemble_asset_table",)},
        ),
        (
            "Description and Texts",
            {
                "classes": ("collapse",),
                "fields": (
                    "description_long",
                    "description_short",
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
            {"classes": ("collapse",), "fields": ("links",)},
        ),
    )

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

    def format_episode_list(self, obj):
        out = """
        <table width="100%">\n
        <tr>
        <th colspan="3">Episodes</th>
        <th>API Link</th>
        <th># Assets</th>
        <th>Last Updated</th>
        <th>API Status
        </tr>
        """

        for episode in obj.episodes.order_by("ordinal"):
            out += episode.create_table_line()
        out += "</table>"
        return mark_safe(out)

    format_episode_list.short_description = "EPISODE LIST"


admin.site.register(Season, PBSMMSeasonAdmin)
