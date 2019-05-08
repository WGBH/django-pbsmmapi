from django.contrib import admin
from django.utils.safestring import mark_safe

from .forms import PBSMMSeasonCreateForm, PBSMMSeasonEditForm
from .models import PBSMMSeason, PBSMMSeasonAsset
from ..abstract.admin import PBSMMAbstractAdmin
from ..asset.admin import PBSMMAbstractAssetAdmin


class PBSMMSeasonAdmin(PBSMMAbstractAdmin):
    form = PBSMMSeasonEditForm
    add_form = PBSMMSeasonCreateForm
    model = PBSMMSeason
    list_display = (
        'pk', 'printable_title', 'show', 'ordinal', 'date_last_api_update',
        'last_api_status_color', 'show_publish_status'
    )
    list_display_links = ('pk', 'printable_title')
    list_filter = ('show__title_sortable',)
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are
    # properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 'last_api_status_color',
        'api_endpoint', 'api_endpoint_link',
        'title', 'title_sortable', 'ordinal',
        'description_long', 'description_short',
        'updated_at', 'last_api_status',
        'images', 'pretty_image_list',
        'canonical_image', 'canonical_image_tag',
        'links',

        'format_episode_list',
        'assemble_asset_table',
        'show_publish_status',
        'show_api_id',
    ]

    add_fieldsets = (
        (None, {'fields': ('object_id', 'show', 'ingest_episodes'), }),
    )

    fieldsets = (
        (None, {
            'fields': (
                ('ingest_on_save', 'ingest_episodes'),
                ('date_created', 'date_last_api_update', 'updated_at',
                 'last_api_status', 'last_api_status_color'),
                'api_endpoint_link',

            ),
        }),
        ('Episodes', {
            'fields': ('format_episode_list', )
        }),
        ('Season Metadata', {  # 'classes': ('collapse in',),
            'fields': (
                'ordinal',
                'show_api_id',
            ),
        }),
        ('Assets', {'fields': ('assemble_asset_table',), }),
        ('Description and Texts', {'classes': ('collapse',),
                                   'fields': (
            'description_long', 'description_short',
        ),
        }),
        ('Images', {'classes': ('collapse',),
                    'fields': (
            'images', 'pretty_image_list',
            'canonical_image_type_override',
            'canonical_image_tag',
        ),
        }),
        ('Other', {'classes': ('collapse',),
                   'fields': (
            'links',
        )
        }),
    )

    # Switch between the fieldsets depending on whether we're adding or
    # viewing a record
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(PBSMMSeasonAdmin, self).get_fieldsets(request, obj)

    # Apply the chosen fieldsets tuple to the viewed form
    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            kwargs.update({
                'form': self.add_form,
                'fields': admin.utils.flatten_fieldsets(self.add_fieldsets),
            })
        defaults.update(kwargs)
        return super(PBSMMSeasonAdmin, self).get_form(request, obj, **kwargs)

    def format_episode_list(self, obj):

        out = '<table width=\"100%\">\n' + \
            '<tr>' +\
            '<th colspan=\"3\">Episodes</th>' + \
            '<th>API Link</th>' + \
            '<th># Assets</th>' + \
            '<th>Last Updated</th>' + \
            '<th>API Status' + \
            '<th>Public</th>' + \
            '</tr>'

        episode_list = obj.episodes.order_by('ordinal')
        for episode in episode_list:
            out += episode.create_table_line()
        out += '</table>'
        return mark_safe(out)
    format_episode_list.short_description = 'EPISODE LIST'


class PBSMMSeasonAssetAdmin(PBSMMAbstractAssetAdmin):
    model = PBSMMSeasonAsset
    list_display = (
        'pk', 'object_id', 'season_title', 'object_type', 'legacy_tp_media_id',
        'asset_publicly_available', 'title_sortable', 'duration'
    )

    def season_title(self, obj):
        return obj.season.title
    season_title.short_description = 'Season'


admin.site.register(PBSMMSeason, PBSMMSeasonAdmin)
admin.site.register(PBSMMSeasonAsset, PBSMMSeasonAssetAdmin)
