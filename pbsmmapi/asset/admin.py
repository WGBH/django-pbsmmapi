from django.contrib import admin
from django.utils.safestring import mark_safe

from pbsmmapi.abstract.admin import AnnotatedReadonlyAdminMixin
from pbsmmapi.asset.models import Asset


class PBSMMAssetAdmin(AnnotatedReadonlyAdminMixin, admin.ModelAdmin):
    model = Asset

    # Almost everything shown here is now a queryset annotation derived from
    # mm_content.api_data rather than a model field. The mixin surfaces each
    # annotated_fields name as a read-only value; we don't want to override
    # what's coming from the API, but we do want to view it in Django.
    annotated_fields = [
        "asset_type",
        "duration",
        "can_embed_player",
        "is_excluded_from_dfp",
        "availability",
        "content_rating",
        "content_rating_description",
        "language",
        "topics",
        "tags",
        "player_code",
        "links",
        "geo_profile",
        "platforms",
        "images",
    ]
    readonly_fields = [
        "asset_publicly_available",
        "date_created",
        "player_code_preview",
        "slug",
        "title",
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
                "fields": ("title", "asset_publicly_available"),
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

    @admin.display(
        boolean=True,
        description="Pub. Avail.",
    )
    def asset_publicly_available(self, obj):
        return obj.asset_publicly_available()


admin.site.register(Asset, PBSMMAssetAdmin)
