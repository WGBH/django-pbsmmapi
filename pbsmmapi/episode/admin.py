from django.contrib import admin
from .models import PBSMMEpisode

class PBSMMShowAdmin(admin.ModelAdmin):
    model = PBSMMEpisode
    list_display = ('pk',  'object_id', 'title_sortable', 'date_last_api_update' )
    list_display_links = ('pk', 'object_id')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 
        'link_to_api_record_link',
        'title', 'title_sortable', 
        'description_long', 'description_short',
    ]
    
    fieldsets = (
        (None, {
            'fields': (
                'ingest_on_save',
                ('date_created','date_last_api_update','updated_at'),
                'link_to_api_record_link',
                'object_id',

            ),
        }),
        ('Metadata', { #'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 'remote_url_link'
            ),
        }),
        ('Description', { 'classes': ('collapse',),
            'fields': (
                'description_long', 'description_short',
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

admin.site.register(PBSMMShow, PBSMMShowAdmin)