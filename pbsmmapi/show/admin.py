from django.contrib import admin
from django.utils.safestring import mark_safe

from pbsmmapi.abstract.admin import PBSMMAbstractAdmin
from pbsmmapi.show.forms import (
    PBSMMShowCreateForm,
    PBSMMShowEditForm,
)
from pbsmmapi.show.models import Show


class PBSMMShowAdmin(PBSMMAbstractAdmin):
    form = PBSMMShowEditForm
    add_form = PBSMMShowCreateForm
    model = Show
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
        "audience",
        "can_embed_player",
        "date_created",
        "date_last_api_update",
        "description_long",
        "description_short",
        "display_episode_number",
        "episode_count",
        "format_seasons_list",
        "format_specials_list",
        "funder_message",
        "ga_event",
        "ga_page",
        "genre",
        "hashtag",
        "images",
        "is_excluded_from_dfp",
        "language",
        "last_api_status_color",
        "links",
        "nola",
        "object_id",
        "ordinal_season",
        "platforms",
        "premiered_on",
        "pretty_image_list",
        "sort_episodes_descending",
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
                    ("ingest_seasons", "ingest_episodes", "ingest_specials"),
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
                        "ingest_seasons",
                        "ingest_specials",
                        "ingest_episodes",
                    ),
                ),
            },
        ),
        (
            "Seasons and Specials",
            {
                "fields": ("format_seasons_list", "format_specials_list"),
            },
        ),
        (
            "Show Metadata",
            {
                "classes": ("collapse in",),
                "fields": (
                    ("slug",),
                    (
                        "episode_count",
                        "display_episode_number",
                        "sort_episodes_descending",
                    ),
                    ("ordinal_season", "is_excluded_from_dfp", "can_embed_player"),
                    ("nola", "premiered_on", "language"),
                ),
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
                    "audience",
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

    def format_seasons_list(self, obj):
        out = """
        <table width="100%" border=2>\n
        <tr style="background-color: #999;">
        <th colspan="3">Season / Episodes</th>
        <th>API Link</th>
        <th># Assets</th>
        <th>Last Updated</th>
        <th>API Status</th>
        </tr>
        """
        for season in obj.seasons.order_by("-ordinal"):
            out += season.create_table_line()
            for episode in season.episodes.order_by("ordinal"):
                out += episode.create_table_line()

        out += "</table>"
        return mark_safe(out)

    format_seasons_list.short_description = "SEASON LIST"

    def format_specials_list(self, obj):
        # It turns out that some shows, e.g., The Open Mind, have an INSANE
        # number of specials. In this case, just return the Top 50
        out = ""
        specials_list = obj.specials.order_by("-premiered_on")
        if specials_list.count() > 100:
            out = "<p>There are %s specials.</p>" % "{:,}".format(specials_list.count())
            out += "<p>Here are the most recent 50 (by premiere date).</p>"
            admin_filter_slug = "/admin/special/pbsmmspecial/?show_slug=%s" % obj.slug
            out += '<p>You can access the entire list at <a href="%s">%s</a>.' % (
                admin_filter_slug,
                admin_filter_slug,
            )
            specials_list_to_show = specials_list[:50]
        else:
            specials_list_to_show = specials_list

        out += """
        <table width="100%" border=2>\n
        <tr style="background-color: #999;">
        <th>Special Title</th>
        <th>API Link</th>
        <th># Assets</th>
        <th>Last Updated</th>
        <th>API Status</th>
        </tr>
        """
        for special in specials_list_to_show:
            out += special.create_table_line()

        out += "</table>"
        return mark_safe(out)

    format_specials_list.short_description = "SPECIALS LIST"


admin.site.register(Show, PBSMMShowAdmin)
