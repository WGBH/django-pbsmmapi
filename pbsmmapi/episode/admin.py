from django.contrib import admin

from pbsmmapi.abstract.admin import PBSMMAbstractAdmin
from pbsmmapi.episode.forms import (
    PBSMMEpisodeCreateForm,
    PBSMMEpisodeEditForm,
)
from pbsmmapi.episode.models import Episode


class PBSMMEpisodeAdmin(PBSMMAbstractAdmin):
    model = Episode
    form = PBSMMEpisodeEditForm
    add_form = PBSMMEpisodeCreateForm

    list_display = (
        "pk",
        "title_sortable",
        "full_episode_code",
        "date_last_api_update",
        "last_api_status_color",
    )
    list_display_links = ("pk", "title_sortable")
    list_filter = ("season__show__title_sortable",)
    # Why so many readonly_fields?  Because we don't want to override what's
    # coming from the API, but we do want to be able to view it in the context
    # of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        "api_endpoint_link",
        "assemble_asset_table",
        "date_created",
        "date_last_api_update",
        "description_long",
        "description_short",
        "encored_on",
        "funder_message",
        "language",
        "last_api_status_color",
        "links",
        "nola",
        "ordinal",
        "premiered_on",
        "segment",
        "slug",
        "title",
        "title_sortable",
        "updated_at",
    ]

    # If we're adding a record - no sense in seeing all the things that aren't
    # there yet, since only these TWO fields are editable anyway...
    add_fieldsets = (
        (
            None,
            {
                "fields": ("object_id", "season"),
            },
        ),
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("object_id", "date_created"),
                    ("date_last_api_update", "updated_at", "last_api_status_color"),
                ),
            },
        ),
        (
            "Title, Slug, Link",
            {
                "fields": (
                    "title",
                    "title_sortable",
                    "slug",
                    "api_endpoint_link",
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
                "fields": ("description_long", "description_short", "funder_message"),
            },
        ),
        (
            "Episode Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    ("premiered_on", "encored_on"),
                    ("nola", "ordinal", "segment"),
                    "language",
                ),
            },
        ),
        (
            "Other",
            {
                "classes": ("collapse",),
                "fields": ("links",),
            },
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

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            return readonly_fields + ["object_id", "legacy_tp_media_id"]
        return self.readonly_fields


admin.site.register(Episode, PBSMMEpisodeAdmin)
