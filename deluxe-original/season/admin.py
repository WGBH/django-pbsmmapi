from django.contrib import admin
from .forms import PBSMMSeasonCreateForm, PBSMMSeasonEditForm
from .models import PBSMMSeason

class PBSMMSeasonAdmin(admin.ModelAdmin):
    form = PBSMMSeasonEditForm
    add_form = PBSMMSeasonCreateForm
    model = PBSMMSeason
    list_display = ('pk',  'object_id',  'ordinal', 'title_sortable', 'date_last_api_update', 'last_api_status_color' )
    list_display_links = ('pk', 'object_id')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 'last_api_status_color', 
        'api_endpoint', 'api_endpoint_link',
        'title', 'title_sortable', 'ordinal',
        'description_long', 'description_short',
        'updated_at', 'last_api_status',
        'images',
        'canonical_image', 'canonical_image_tag',
        'links'
    ]
    
    add_fieldsets = (
        (None, {'fields': ('object_id',),} ),
    )
    
    fieldsets = (
        (None, {
            'fields': (
                'ingest_on_save',
                ('date_created','date_last_api_update','updated_at', 'last_api_status', 'last_api_status_color'),
                'api_endpoint_link',
                'object_id',

            ),
        }),
        ('Season Metadata', { #'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable',
                'ordinal'
            ),
        }),
        ('Description and Texts', { 'classes': ('collapse',),
            'fields': (
                'description_long', 'description_short',
            ),
        }),
        ('Images', { 'classes': ('collapse',),
            'fields': (
                'images',
                'canonical_image', 'canonical_image_tag',
            ),
        }),
        ('Other', { 'classes': ('collapse',),
            'fields': (
                'links',
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

admin.site.register(PBSMMSeason, PBSMMSeasonAdmin)