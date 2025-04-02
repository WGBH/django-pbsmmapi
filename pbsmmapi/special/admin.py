from django.contrib import admin

from pbsmmapi.abstract.admin import PBSMMAbstractAdmin
from pbsmmapi.special.forms import (
    PBSMMSpecialCreateForm,
    PBSMMSpecialEditForm,
)
from pbsmmapi.special.models import Special


class PBSMMSpecialAdmin(PBSMMAbstractAdmin):
    model = Special
    form = PBSMMSpecialEditForm
    add_form = PBSMMSpecialCreateForm
    list_filter = ("show__slug",)

    list_display = (
        "pk",
        "title_sortable",
        "show",
        "premiered_on",
        "date_last_api_update",
        "last_api_status_color",
    )
    list_display_links = ("pk", "title_sortable")
    # Why so many readonly_fields?  Because we don't want to override what's
    # coming from the API, but we do want to be able to view it in the context
    # of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        "date_created",
        "date_last_api_update",
        "last_api_status",
        "api_endpoint_link",
        "last_api_status_color",
        "title",
        "title_sortable",
        "description_long",
        "description_short",
        "updated_at",
        "premiered_on",
        "links",
        "language",
        "nola",
        "assemble_asset_table",
    ]

    # If we're adding a record - no sense in seeing all the things that aren't
    # there yet, since only these TWO fields are editable anyway...
    add_fieldsets = (
        (
            None,
            {
                "fields": ("slug", "show"),
            },
        ),
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "ingest_on_save",
                    (
                        "date_created",
                        "date_last_api_update",
                        "updated_at",
                        "last_api_status_color",
                    ),
                    "object_id",
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
                "fields": (
                    "description_long",
                    "description_short",
                ),
            },
        ),
        (
            "Special Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    ("premiered_on", "nola"),
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


admin.site.register(Special, PBSMMSpecialAdmin)
