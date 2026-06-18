from django.contrib import admin
from django.utils.safestring import mark_safe

from pbsmmapi.asset.helpers import check_asset_availability
from pbsmmapi.asset.models import Asset


class PBSMMAssetAdmin(admin.ModelAdmin):
    model = Asset

    # Why so many readonly_fields?  Because we don't want to override what's
    # coming from the API, but we do want to be able to view it in the context
    # of the Django system.
    #
    # Most things here are annotated fields.
    readonly_fields = [
        "asset_publicly_available",
        "content_rating",
        "content_rating_description",
        "date_created",
        "player_code_preview",
        "slug",
        "title",
        "topics",
    ]
    search_fields = ("title",)

    # If we're viewing a record, make it pretty.
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "ingest_on_save",
                    ("date_created",),
                ),
            },
        ),
        (
            "Title and Availability",
            {
                "fields": ("title",),
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
            "Description",
            {
                "classes": ("collapse",),
                "fields": ("slug",),
            },
        ),
        (
            "Asset Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    ("asset_type", "duration"),
                    ("can_embed_player", "is_excluded_from_dfp"),
                    "availability",
                    "content_rating",
                    "content_rating_description",
                    "language",
                    "topics",
                    "tags",
                ),
            },
        ),
        (
            "Asset Preview",
            {
                "classes": ("collapse",),
                "fields": (
                    "player_code",
                    "player_code_preview",
                ),
            },
        ),
        (
            "Additional Metadata",
            {
                "classes": ("collapse",),
                "fields": ("links", "geo_profile", "platforms"),
            },
        ),
    ]

    def player_code_preview(self, obj):
        out = ""
        if obj.player_code and len(obj.player_code) > 1:
            out += '<div style="width:640px; height: 360px;">'
            out += obj.player_code
            out += "</div>"
        return mark_safe(out)

    def platforms(self, obj):
        return obj.platforms

    def topics(self, obj):
        return obj.topics

    def availability(self, obj):
        return obj.availability

    def player_code(self, obj):
        return obj.player_code

    def images(self, obj):
        return obj.images

    def content_rating(self, obj):
        return obj.content_rating

    def content_rating_description(self, obj):
        return obj.content_rating_description

    def is_excluded_from_dfp(self, obj):
        return obj.is_excluded_from_dfp

    @admin.display(
        boolean=True,
        description="Pub. Avail.",
    )
    def asset_publicly_available(self, obj):
        if obj.availability:
            public_window = obj.availability.get("public", None)
            if public_window:
                return check_asset_availability(
                    start=public_window["start"],
                    end=public_window["end"],
                )[0]
        return None


admin.site.register(Asset, PBSMMAssetAdmin)
