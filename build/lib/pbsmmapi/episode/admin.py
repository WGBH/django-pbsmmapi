from django.contrib import admin

from ..abstract.admin import PBSMMAbstractAdmin
from ..asset.admin import PBSMMAbstractAssetAdmin
from .models import PBSMMEpisode, PBSMMEpisodeAsset
from .forms import PBSMMEpisodeCreateForm, PBSMMEpisodeEditForm


class PBSMMEpisodeAdmin(PBSMMAbstractAdmin):
    model = PBSMMEpisode
    form = PBSMMEpisodeEditForm
    add_form = PBSMMEpisodeCreateForm

    list_display = (
        'pk',
        'title_sortable',
        'full_episode_code',
        'date_last_api_update',
        'last_api_status_color',
        'show_publish_status')
    list_display_links = ('pk', 'title_sortable')
    list_filter = ('season__show__title_sortable',)
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are
    # properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 'last_api_status_color',
        'api_endpoint_link',
        'title', 'title_sortable', 'slug', 'api_endpoint_link',
        'description_long', 'description_short', 'funder_message',
        'premiered_on', 'encored_on', 'nola', 'language',
        'links', 'ordinal', 'segment',

        'assemble_asset_table', 'canonical_image_tag', 'images', 'show_publish_status'
    ]

    # If we're adding a record - no sense in seeing all the things that aren't there yet, since only these TWO
    # fields are editable anyway...
    add_fieldsets = (
        (None, {'fields': ('object_id', 'season'), }),
    )

    fieldsets = (
        (None, {
            'fields': (
                ('object_id', 'date_created', 'api_endpoint_link',),
                ('date_last_api_update', 'updated_at', 'last_api_status_color'),
            ),
        }),
        ('Administration', {
            'fields': (
                ('publish_status', 'live_as_of', ),
            ),
        }),
        ('Title, Slug, Link', {  # 'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 'slug', 'api_endpoint_link'
            ),
        }),
        ('Assets', {'fields': ('assemble_asset_table',), }),
        ('Images', {'classes': ('collapse',),
                    'fields': (
            'images',
            'canonical_image_type_override',
            'canonical_image_tag',
        ),
        }),
        ('Description and Texts', {'classes': ('collapse',),
                                   'fields': (
            'description_long', 'description_short',
            'funder_message'
        ),
        }),
        ('Episode Metadata', {'classes': ('collapse',),
                              'fields': (
            ('premiered_on', 'encored_on'),
            ('nola', 'ordinal', 'segment'),
            'language',
        ),
        }),
        ('Other', {'classes': ('collapse',),
                   'fields': (
            'links',
        ),
        }),

    )

    # Switch between the fieldsets depending on whether we're adding or
    # viewing a record
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(PBSMMEpisodeAdmin, self).get_fieldsets(request, obj)

    # Apply the chosen fieldsets tuple to the viewed form
    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            kwargs.update({
                'form': self.add_form,
                'fields': admin.utils.flatten_fieldsets(self.add_fieldsets),
            })
        defaults.update(kwargs)
        return super(PBSMMEpisodeAdmin, self).get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(
            PBSMMEpisodeAdmin,
            self).get_readonly_fields(
            request,
            obj)
        if obj:
            return readonly_fields + ['object_id', 'legacy_tp_media_id']
        else:
            return self.readonly_fields


class PBSMMEpisodeAssetAdmin(PBSMMAbstractAssetAdmin):
    model = PBSMMEpisodeAsset
    list_display = (
        'pk', 'object_id', 'full_episode_code', 'object_type',
        'legacy_tp_media_id', 'asset_publicly_available', 'title_sortable',
        'duration'
    )

    def full_episode_code(self, obj):
        return obj.episode.full_episode_code
    full_episode_code.short_description = 'Episode'


admin.site.register(PBSMMEpisode, PBSMMEpisodeAdmin)
admin.site.register(PBSMMEpisodeAsset, PBSMMEpisodeAssetAdmin)
