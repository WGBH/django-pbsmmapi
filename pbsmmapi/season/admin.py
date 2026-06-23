from django.contrib import admin
from django.utils.safestring import mark_safe

from pbsmmapi.abstract.admin import (
    AnnotatedReadonlyAdminMixin,
    PBSMMAbstractAdmin,
)
from pbsmmapi.season.forms import (
    PBSMMSeasonCreateForm,
    PBSMMSeasonEditForm,
)
from pbsmmapi.season.models import Season


class PBSMMSeasonAdmin(AnnotatedReadonlyAdminMixin, PBSMMAbstractAdmin):
    form = PBSMMSeasonEditForm
    add_form = PBSMMSeasonCreateForm
    model = Season
    list_display = (
        "pk",
        "printable_title",
        "show",
        "ordinal",
    )
    list_display_links = ("pk", "printable_title")
    list_filter = ("show__title",)
    # The metadata shown here is now exposed via queryset annotations; the
    # mixin surfaces each annotated_fields name as a read-only value. We don't
    # want to override what's coming from the API, but we do want to view it.
    annotated_fields = [
        "description_long",
        "description_short",
        "images",
        "links",
        "show_content_id",
    ]
    readonly_fields = [
        "assemble_asset_table",
        "date_created",
        "format_episode_list",
        "ordinal",
        "title",
    ]

    add_fieldsets = (
        (
            None,
            {
                "fields": ("show", "ingest_episodes"),
            },
        ),
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("ingest_on_save", "ingest_episodes"),
                    ("date_created",),
                ),
            },
        ),
        (
            "Episodes",
            {"fields": ("format_episode_list",)},
        ),
        (
            "Season Metadata",
            {"fields": ("ordinal", "show_content_id")},
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
                "fields": ("images",),
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
