from django.contrib import admin
from .forms import PBSMMSeasonCreateForm, PBSMMSeasonEditForm
from .models import PBSMMSeason, PBSMMSeasonAsset

class PBSMMSeasonAdmin(admin.ModelAdmin):
    form = PBSMMSeasonEditForm
    add_form = PBSMMSeasonCreateForm
    model = PBSMMSeason
    list_display = ('pk',  'object_id', 'show', 'ordinal', 
        'title_sortable', 'date_last_api_update', 'last_api_status_color' )
    list_display_links = ('pk', 'object_id')
    readonly_fields = [
        'title', 'api_endpoint', 'date_created', 
        'date_last_api_update', 'last_api_status', 'last_api_status_color', 
        'link_to_api_record', 'title_sortable', 'object_id', 
        'format_episode_list'
    ]
    
    add_fieldsets = (
        (None, {'fields': ('object_id', 'show', 'ingest_episodes'),} ),
    )
    
    fieldsets = (
        (None, {
            'fields': (
                ('ingest_on_save', 'ingest_episodes'),
                ('date_created','date_last_api_update', 'last_api_status', 'last_api_status_color'),
                'link_to_api_record',
                'object_id', 'ordinal'
            ),
        }),
        ('Episodes', {
            'fields': ('format_episode_list', )
        }),
    )

    actions = ['force_reingest',]

    def force_reingest(self, request, queryset):
        # queryset is the list of Asset items that were selected.
        for item in queryset:
            item.ingest_on_save = True
            
            # HOW DO I FIND OUT IF THE save() was successful?
            item.save()
            
    force_reingest.short_description = 'Reingest selected items.'
    
    # Switch between the fieldsets depending on whether we're adding or viewing a record
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
                '<th>Admin</th>' + \
                '<th># Assets</th>' + \
                '<th>Last Updated</th>' + \
                '<th>API Status' + \
                '<th>Public</th>' + \
                '</tr>'

        episode_list = obj.episodes.order_by('ordinal')
        for episode in episode_list:
            out += episode.create_table_line()
        out += '</table>'
        return out
    format_episode_list.allow_tags = True
    format_episode_list.short_description = 'EPISODE LIST'

admin.site.register(PBSMMSeason, PBSMMSeasonAdmin)
admin.site.register(PBSMMSeasonAsset)