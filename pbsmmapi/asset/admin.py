from django.contrib import admin
from .models import PBSMMAsset
from .forms import PBSMMAssetCreateForm, PBSMMAssetEditForm

### TO BE DONE:
# 
# It'd be great to have a listing page function defined so that you could check multiple records and have
# the back end re-ingest them.

class PBSMMAssetAdmin(admin.ModelAdmin):
    form = PBSMMAssetEditForm
    add_form = PBSMMAssetCreateForm
    model = PBSMMAsset
    list_display = ('pk',  'object_id', 'legacy_tp_media_id', 'asset_publicly_available', 
        'title_sortable', 'duration', 'date_last_api_update' )
    list_display_links = ('pk', 'object_id')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'updated_at', 
        'link_to_api_record_link',
        'title', 'title_sortable', 'slug', 'object_type',
        'description_long', 'description_short',
        'is_excluded_from_dfp', 'can_embed_player', 
        'player_code', 'language',
        'duration', 'tags', 'availability', 'asset_publicly_available',
        'links', 'chapters', 'images', 'canonical_image', 'canonical_image_tag',
        'content_rating', 'content_rating_description', 'topics', 'geo_profile',
        'platforms', 'windows'
    ]
    
    # If we're adding a record - no sense in seeing all the things that aren't there yet, since only these TWO
    # fields are editable anyway...
    add_fieldsets = (
        (None, {'fields': ('object_id', 'legacy_tp_media_id'),} ),
    )
    
    # If we're viewing a record, make it pretty.
    fieldsets = (
        (None, {
            'fields': (
                'ingest_on_save',
                ('date_created','date_last_api_update','updated_at'),
                'link_to_api_record_link',
                ('object_id', 'legacy_tp_media_id'),
            ),
        }),
        ('Title and Availability', { #'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 
                'asset_publicly_available', 
            ),
        }),
        ('Images', { 'classes': ('collapse',),
            'fields': (
                'images',
                'canonical_image', 'canonical_image_tag',
            ),
        }),
        ('Description', { 'classes': ('collapse',),
            'fields': (
                'slug','description_long', 'description_short',
            ),
        }),
        ('Asset Metadata', { 'classes': ('collapse',),
            'fields': (
                ('object_type', 'duration'), 
                ('can_embed_player', 'is_excluded_from_dfp'),
                'player_code',
                'availability',
                'content_rating',
                'content_rating_description',
                'language',
                'topics', 'tags', 'chapters', 
            ),
        }),
        ('Additional Metadata', { 'classes': ('collapse',),
            'fields': (
                'links', 'geo_profile', 'platforms', 'windows'
            )
        }),
    )
    actions = ['force_reingest',]
    
    def force_reingest(self, request, queryset):
        # queryset is the list of Asset items that were selected.
        number_scraped = 0
        for item in queryset:
            item.ingest_on_save = True
            item.save()
    force_reingest.short_description = 'Reingest selected items.'
    
    # Switch between the fieldsets depending on whether we're adding or viewing a record
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(PBSMMAssetAdmin, self).get_fieldsets(request, obj)
        
    # Apply the chosen fieldsets tuple to the viewed form
    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            kwargs.update({
                'form': self.add_form,
                'fields': admin.utils.flatten_fieldsets(self.add_fieldsets),
            })
        defaults.update(kwargs)
        return super(PBSMMAssetAdmin, self).get_form(request, obj, **kwargs)
        
admin.site.register(PBSMMAsset, PBSMMAssetAdmin)