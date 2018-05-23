from django.contrib import admin
from .models import PBSMMSpecial
from .forms import PBSMMSpecialCreateForm, PBSMMSpecialEditForm
class PBSMMSpecialAdmin(admin.ModelAdmin):
    model = PBSMMSpecial
    form = PBSMMSpecialEditForm
    add_form = PBSMMSpecialCreateForm
    
    list_display = ('pk',  'object_id', 'title_sortable', 'date_last_api_update', 'last_api_status_color' )
    list_display_links = ('pk', 'object_id')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'last_api_status', 'api_endpoint_link', 'last_api_status_color',
        'title', 'title_sortable', 'slug', 
        'description_long', 'description_short', 
        'updated_at', 'premiered_on', 
        #'images', 'funder_message',
        #'is_excluded_from_dfp', 'can_embed_player', 
        'links', 
        #'platforms', 'ga_page', 'ga_event', 'genre', 'episode_count',
        #'display_episode_number', 'sort_episodes_descending', 
        #'ordinal_season', 
        'language', 
        #'audience', 'hashtag',
        #'canonical_image_tag',
        'encored_on', 'nola',
    ]
    
    # If we're adding a record - no sense in seeing all the things that aren't there yet, since only these TWO
    # fields are editable anyway...
    add_fieldsets = (
        (None, {'fields': ('object_id',),} ),
    )
    
    fieldsets = (
        (None, {
            'fields': (
                'ingest_on_save',
                ('date_created','date_last_api_update','updated_at', 'last_api_status_color'),
                'api_endpoint_link',
                'object_id',

            ),
        }),
        ('Title, Slug, Link', { #'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 'slug', 'api_endpoint_link', 'last_api_status_color'
            ),
        }),
        ('Description and Texts', { 'classes': ('collapse',),
            'fields': (
                'description_long', 'description_short',
                #'funder_message'
            ),
        }),
        #('Images', {'classes': ('collapse',),
        #    'fields': (
        #        'images', 'canonical_image_tag'
        #    )
        #}),
        ('Special Metadata', { 'classes': ('collapse',),
            'fields': (
                ('premiered_on', 'encored_on', 'nola'),
                #'is_excluded_from_dfp', 'can_embed_player'),
                #('display_episode_number', 'sort_episodes_descending', 'ordinal_season'),
                #'episode_count', 
                #('hashtag', 'ga_page', 'ga_event'),
                'language',
            ),
        }),
        ('Other', { 'classes': ('collapse',),
            'fields': (
                'links',
                #'audience', 
                #'genre',
                #'platforms', 
            ),
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
        return super(PBSMMSpecialAdmin, self).get_fieldsets(request, obj)
        
    # Apply the chosen fieldsets tuple to the viewed form
    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            kwargs.update({
                'form': self.add_form,
                'fields': admin.utils.flatten_fieldsets(self.add_fieldsets),
            })
        defaults.update(kwargs)
        return super(PBSMMSpecialAdmin, self).get_form(request, obj, **kwargs)

admin.site.register(PBSMMSpecial, PBSMMSpecialAdmin)