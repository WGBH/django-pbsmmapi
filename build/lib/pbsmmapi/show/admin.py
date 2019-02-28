from django.contrib import admin
from django.utils.safestring import mark_safe

from ..abstract.admin import PBSMMAbstractAdmin
from ..asset.admin import PBSMMAbstractAssetAdmin
from .forms import PBSMMShowCreateForm, PBSMMShowEditForm
from .models import PBSMMShow, PBSMMShowAsset


class ShowAssetInline(admin.TabularInline):
    model = PBSMMShowAsset
    fieldsets = (
        (None, {
            'fields': (
                ('id',
                 'title',
                 'object_type',
                 'formatted_duration',
                 'asset_publicly_available'),
            ),
        }),
    )
    readonly_fields = [
        'id',
        'title',
        'object_type',
        'formatted_duration',
        'asset_publicly_available']
    extra = 0


class PBSMMShowAdmin(PBSMMAbstractAdmin):
    form = PBSMMShowEditForm
    add_form = PBSMMShowCreateForm
    model = PBSMMShow
    # inlines = [ShowAssetInline,]
    list_display = ('pk', 'slug', 'object_id', 'title_sortable',
                    'show_publish_status', 'date_last_api_update', 'last_api_status_color')
    list_display_links = ('pk', 'slug', 'object_id')
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 'last_api_status_color',
        'api_endpoint', 'api_endpoint_link', 'object_id',
        'title', 'title_sortable',
        'description_long', 'description_short',
        'updated_at', 'premiered_on', 'nola',
        'images', 'canonical_image_tag',
        'funder_message',
        'is_excluded_from_dfp', 'can_embed_player',
        'links', 'platforms', 'ga_page', 'ga_event', 'genre',

        'episode_count', 'display_episode_number', 'sort_episodes_descending',
        'ordinal_season', 'language', 'audience', 'hashtag',

        'format_seasons_list', 'format_specials_list', 'pretty_image_list',
        'assemble_asset_table', 'show_publish_status'
    ]
    add_readonly_fields = []
    add_fieldsets = (
        (None, {
            'fields': (
                'slug',
                ('ingest_seasons', 'ingest_episodes', 'ingest_specials'),
            ),
        }),
    )

    fieldsets = (
        (None, {
            'fields': (
                ('title', 'title_sortable',),
                ('object_id', 'date_created', 'api_endpoint_link',),
                ('date_last_api_update', 'updated_at', 'last_api_status_color'),
            ),
        }),
        ('Administration', {
            'fields': (
                ('ingest_on_save', 'ingest_seasons',
                 'ingest_specials', 'ingest_episodes'),
                ('publish_status', 'live_as_of', )
            ),
        }),
        ('Seasons and Specials', {
            # 'classes': ('collapse in',),
            'fields': ('format_seasons_list', 'format_specials_list'),
        }),
        ('Show Metadata', {
            'classes': ('collapse in',),
            'fields': (
                ('slug', 'title', 'title_sortable'),
                ('episode_count',
                 'display_episode_number',
                 'sort_episodes_descending'),
                ('ordinal_season', 'is_excluded_from_dfp', 'can_embed_player'),
                ('nola', 'premiered_on', 'language'),

            ),
        }),
        ('Assets', {'fields': ('assemble_asset_table',), }),
        ('Description and Texts', {'classes': ('collapse',),
                                   'fields': (
            'description_long', 'description_short', 'funder_message',
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
            'audience',
            'hashtag',
            ('ga_page', 'ga_event'),
            'genre',
            'links',
            'platforms',
        )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.add_readonly_fields
        return super(PBSMMShowAdmin, self).get_readonly_fields(request, obj)

    # Switch between the fieldsets depending on whether we're adding or
    # viewing a record
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(PBSMMShowAdmin, self).get_fieldsets(request, obj)

    # Apply the chosen fieldsets tuple to the viewed form
    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            kwargs.update({
                'form': self.add_form,
                'fields': admin.utils.flatten_fieldsets(self.add_fieldsets),
            })
        defaults.update(kwargs)
        return super(PBSMMShowAdmin, self).get_form(request, obj, **kwargs)

#####################################################
# Create a highly formated table of children/relationships
#####################################################
    def format_seasons_list(self, obj):
        out = '<table width=\"100%\" border=2>\n' + \
            '<tr style=\"background-color: #999;\">' +\
            '<th colspan=\"3\">Season / Episodes</th>' + \
            '<th>API Link</th>' + \
            '<th># Assets</th>' + \
            '<th>Last Updated</th>' + \
            '<th>API Status' + \
            '<th>Public</th>' + \
            '</tr>'
        season_list = obj.seasons.order_by('-ordinal')
        for season in season_list:
            x = season.create_table_line()
            out = out + x

            episode_list = season.episodes.order_by('ordinal')
            for episode in episode_list:
                x = episode.create_table_line()
                out += episode.create_table_line()

        out += '</table>'
        return mark_safe(out)
    format_seasons_list.short_description = 'SEASON LIST'

    def format_specials_list(self, obj):
        # It turns out that some shows, e.g., The Open Mind, have an INSANE number of specials.
        # In this case, just return the Top 50
        out = ''
        specials_list = obj.specials.order_by('-premiered_on')
        if specials_list.count() > 100:
            out = '<p>There are %s specials.</p>' % "{:,}".format(
                specials_list.count())
            out += '<p>Here are the most recent 50 (by premiere date).</p>'
            admin_filter_slug = '/admin/special/pbsmmspecial/?show_slug=%s' % obj.slug
            out += '<p>You can access the entire list at <a href=\"%s\">%s</a>.' % (
                admin_filter_slug, admin_filter_slug)
            specials_list_to_show = specials_list[:50]
        else:
            specials_list_to_show = specials_list

        out += '<table width=\"100%\" border=2>\n' + \
            '<tr style=\"background-color: #999;\">' +\
            '<th>Special Title</th>' + \
            '<th>API Link</th>' + \
            '<th># Assets</th>' + \
            '<th>Last Updated</th>' + \
            '<th>API Status' + \
            '<th>Public</th>' + \
            '</tr>'
        for special in specials_list_to_show:
            out += special.create_table_line()

        out += '</table>'
        return mark_safe(out)
    format_specials_list.short_description = 'SPECIALS LIST'


class PBSMMShowAssetAdmin(PBSMMAbstractAssetAdmin):
    model = PBSMMShowAsset
    list_display = ('pk', 'object_id', 'show_title', 'object_type', 'legacy_tp_media_id', 'asset_publicly_available',
                    'title_sortable', 'duration')

    def show_title(self, obj):
        return obj.show.title
    show_title.short_description = 'Show'


admin.site.register(PBSMMShow, PBSMMShowAdmin)
admin.site.register(PBSMMShowAsset, PBSMMShowAssetAdmin)
