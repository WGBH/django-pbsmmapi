from django.contrib import admin

from ..abstract.admin import get_abstract_asset_table
from .models import PBSMMEpisode, PBSMMEpisodeAsset
from .forms import PBSMMEpisodeCreateForm, PBSMMEpisodeEditForm

class PBSMMEpisodeAdmin(admin.ModelAdmin):
    model = PBSMMEpisode
    form = PBSMMEpisodeEditForm
    add_form = PBSMMEpisodeCreateForm
    list_display = ('pk',  'object_id', 'episode_code', 'title_sortable', 'date_last_api_update', 'last_api_status_color')
    list_display_links = ('pk', 'object_id')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'last_api_status_color', 
        'title', 'title_sortable', 'slug',
        'link_to_api_record', 'ordinal',
        'assemble_episode_asset_table'
    ]
    
    # If we're adding a record - no sense in seeing all the things that aren't there yet, since only these TWO
    # fields are editable anyway...
    add_fieldsets = (
        (None, {'fields': ('object_id', 'season'),} ),
    )

    fieldsets = (
        (None, {
            'fields': (
                ('ingest_on_save',),
                ('date_created','date_last_api_update','last_api_status_color'),
                'link_to_api_record',
                ('object_id', 'ordinal'),
            ),
        }),
        ('Title, Slug, Link', { #'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 'slug',
            ),
        }),
        ('Assets', {'fields': ('assemble_episode_asset_table',),}),
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
        readonly_fields = super(PBSMMEpisodeAdmin, self).get_readonly_fields(request, obj)
        if obj:
            return readonly_fields + ['object_id','legacy_tp_media_id']
        else:
            return self.readonly_fields
            
    def assemble_episode_asset_table(self, obj):
        asset_list = obj.assets.all()
        print "LIST: ", asset_list
        out = get_abstract_asset_table(asset_list)
        print "OUT: ", out
        return out
    assemble_episode_asset_table.allow_tags = True

admin.site.register(PBSMMEpisode, PBSMMEpisodeAdmin)
admin.site.register(PBSMMEpisodeAsset)


