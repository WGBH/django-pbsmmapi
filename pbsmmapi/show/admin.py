from django.contrib import admin
from .forms import PBSMMShowCreateForm, PBSMMShowEditForm
from .models import PBSMMShow

class PBSMMShowAdmin(admin.ModelAdmin):
    form = PBSMMShowEditForm
    add_form = PBSMMShowCreateForm
    model = PBSMMShow
    list_display = ('pk',  'object_id', 'title_sortable', 'date_last_api_update' )
    list_display_links = ('pk', 'object_id')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 
        'link_to_api_record', 'link_to_api_record_link',
        'title', 'title_sortable', 'slug',
        'description_long', 'description_short',
        'updated_at', 'premiered_on', 'nola', 
        'images', 'canonical_image_tag',
        'funder_message',
        'is_excluded_from_dfp', 'can_embed_player', 
        'links', 'platforms', 'ga_page', 'ga_event', 'genre',
        'episode_count', 'display_episode_number', 'sort_episodes_descending', 
        'ordinal_season', 'language', 'audience', 'hashtag', 'last_api_status'
    ]
    
    add_fieldsets = (
        (None, {'fields': ('object_id',),} ),
    )
    
    fieldsets = (
        (None, {
            'fields': (
                'ingest_on_save',
                ('date_created','date_last_api_update','updated_at', 'last_api_status'),
                'link_to_api_record_link',
                'object_id',

            ),
        }),
        ('Show Metadata', { #'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 
                'slug', 
                ('episode_count', 'display_episode_number', 'sort_episodes_descending'),
                ('ordinal_season', 'is_excluded_from_dfp', 'can_embed_player'),
                ('nola', 'premiered_on', 'language'), 

            ),
        }),
        ('Description and Texts', { 'classes': ('collapse',),
            'fields': (
                'description_long', 'description_short', 'funder_message',
            ),
        }),
        ('Images', {'classes': ('collapse',),
            'fields': (
                'images', 'canonical_image_tag'
            )
        }),
        ('Other', { 'classes': ('collapse',),
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

admin.site.register(PBSMMShow, PBSMMShowAdmin)