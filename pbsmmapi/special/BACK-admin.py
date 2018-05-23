from django.contrib import admin
from .forms import PBSMMSpecialCreateForm, PBSMMSpecialEditForm
from .models import PBSMMSpecial, PBSMMSpecialAsset

class PBSMMSpecialAdmin(admin.ModelAdmin):
    form = PBSMMSpecialEditForm
    add_form = PBSMMSpecialCreateForm
    model = PBSMMSpecial
    list_display = ('pk',  'object_id',  'show', 'title_sortable', 'date_last_api_update', 'last_api_status_color' )
    list_display_links = ('pk', 'object_id')
    
    add_fieldsets = (
        (None, {'fields': ('object_id', 'show'),} ),
    )
    readonly_fields = [
        'title', 'api_endpoint', 'date_created', 
        'date_last_api_update', 'last_api_status', 'last_api_status_color', 
        'link_to_api_record', 'title_sortable', 'object_id', 
    ]
    fieldsets = (
        (None, {
            'fields': (
                'ingest_on_save',
                ('date_created','date_last_api_update', 'last_api_status', 'last_api_status_color'),
                'link_to_api_record',
                'object_id',
                'title'
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
admin.site.register(PBSMMSpecialAsset)