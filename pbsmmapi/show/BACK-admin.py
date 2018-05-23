from django.contrib import admin
from ..abstract.admin import PBSMMAbstractAdmin
from .forms import PBSMMShowCreateForm, PBSMMShowEditForm
from .models import PBSMMShow, PBSMMShowAsset

class PBSMMShowAdmin(PBSMMAbstractAdmin):
    form = PBSMMShowEditForm
    add_form = PBSMMShowCreateForm
    model = PBSMMShow
    list_display = ('pk', 'slug',  'object_id', 'title_sortable', 
        'publish_status', 'date_last_api_update', 'last_api_status_color')
    list_display_links = ('pk', 'slug', 'object_id')
    readonly_fields = [
        'title', 'api_endpoint', 'date_created', 
        'date_last_api_update', 'last_api_status', 'last_api_status_color', 
        'link_to_api_record', 'title_sortable', 'object_id', 
        'format_seasons_list', 'format_specials_list'
    ]
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
                ('ingest_on_save', 'ingest_seasons', 'ingest_specials', 'ingest_episodes'),
                ('date_created', 'date_last_api_update', 'last_api_status_color'),
                ('title', 'title_sortable'), 
                'link_to_api_record',
                ('slug','object_id'),
            ),
        }),
        ('Seasons and Episodes', {'fields': ('format_seasons_list', 'format_specials_list'),}),
    )
    actions = ['force_reingest', 'make_publicly_available','take_offline']


    
    # Switch between the fieldsets depending on whether we're adding or viewing a record
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
### Create a highly formated table of children/relationships
#####################################################
    def format_seasons_list(self, obj):

        out = '<table width=\"100%\" border=2>\n' + \
                '<tr style=\"background-color: #999;\">' +\
                '<th colspan=\"3\">Season / Episodes</th>' + \
                '<th>API Link</th>' + \
                '<th>Admin</th>' + \
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
        return out
    format_seasons_list.allow_tags = True
    format_seasons_list.short_description = 'SEASON LIST'
    
    def format_specials_list(self, obj):
        out =  '<table width=\"100%\" border=2>\n' + \
                '<tr style=\"background-color: #999;\">' +\
                '<th>Special Title</th>' + \
                '<th>API Link</th>' + \
                '<th>Admin</th>' + \
                '<th># Assets</th>' + \
                '<th>Last Updated</th>' + \
                '<th>API Status' + \
                '<th>Public</th>' + \
            '</tr>' 
        for special in obj.specials.all():
            out += special.create_table_line()

        out += '</table>'
        return out
    format_specials_list.allow_tags = True
    format_specials_list.short_description = 'SPECIALS LIST'
    
admin.site.register(PBSMMShow, PBSMMShowAdmin)
admin.site.register(PBSMMShowAsset)