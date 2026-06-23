from django.contrib import admin

from pbsmmapi.abstract.admin import (
    AnnotatedReadonlyAdminMixin,
    PBSMMAbstractAdmin,
)
from pbsmmapi.episode.forms import (
    PBSMMEpisodeCreateForm,
    PBSMMEpisodeEditForm,
)
from pbsmmapi.episode.models import Episode


class PBSMMEpisodeAdmin(AnnotatedReadonlyAdminMixin, PBSMMAbstractAdmin):
    model = Episode
    form = PBSMMEpisodeEditForm
    add_form = PBSMMEpisodeCreateForm

    list_display = (
        "pk",
        "title",
        "full_episode_code",
    )
    list_display_links = ("pk", "title")
    list_filter = ("season__show__title",)
    # The metadata shown here is now exposed via queryset annotations; the
    # mixin surfaces each annotated_fields name as a read-only value. We don't
    # want to override what's coming from the API, but we do want to view it.
    annotated_fields = [
        "description_long",
        "description_short",
        "premiered_on",
        "encored_on",
        "nola",
        "language",
        "links",
    ]
    readonly_fields = [
        "assemble_asset_table",
        "date_created",
        "ordinal",
        "slug",
        "title",
    ]

    # If we're adding a record - no sense in seeing all the things that aren't
    # there yet, since only these TWO fields are editable anyway...
    add_fieldsets = (
        (
            None,
            {
                "fields": ("season",),
            },
        ),
    )

    fieldsets = (
        (
            "Title, Slug, Link",
            {
                "fields": (
                    "title",
                    "slug",
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
                ),
            },
        ),
        (
            "Episode Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    ("premiered_on", "encored_on"),
                    (
                        "nola",
                        "ordinal",
                    ),
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


admin.site.register(Episode, PBSMMEpisodeAdmin)
