from django.contrib import admin
from .models import PBSMMEpisode
from .forms import PBSMMEpisodeCreateForm, PBSMMEpisodeEditForm
class PBSMMEpisodeAdmin(admin.ModelAdmin):
    model = PBSMMEpisode
    form = PBSMMEpisodeEditForm
    add_form = PBSMMEpisodeCreateForm
    list_display = ('pk',  'object_id', 'title_sortable', 'date_last_api_update' )
    list_display_links = ('pk', 'object_id')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 
        'link_to_api_record_link',
        'title', 'title_sortable', 'slug', 'link_to_api_record_link',
        'description_long', 'description_short', 'funder_message',
        'premiered_on', 'encored_on', 'nola', 'language', 
        'links', 'ordinal', 'segment'
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
                ('date_created','date_last_api_update','updated_at'),
                'link_to_api_record_link',
                'object_id',

            ),
        }),
        ('Title, Slug, Link', { #'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 'slug', 'link_to_api_record_link'
            ),
        }),
        ('Description and Texts', { 'classes': ('collapse',),
            'fields': (
                'description_long', 'description_short',
                'funder_message'
            ),
        }),
        ('Episode Metadata', { 'classes': ('collapse',),
            'fields': (
                ('premiered_on', 'encored_on'),
                ('nola', 'ordinal', 'segment'),
                'language',
            ),
        }),
        ('Other', { 'classes': ('collapse',),
            'fields': (
                'links',
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

admin.site.register(PBSMMEpisode, PBSMMEpisodeAdmin)