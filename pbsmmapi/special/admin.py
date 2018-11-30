from django.contrib import admin
from .forms import PBSMMSpecialCreateForm, PBSMMSpecialEditForm
from .models import PBSMMSpecial, PBSMMSpecialAsset
from ..abstract.admin import PBSMMAbstractAdmin
from ..asset.admin import PBSMMAbstractAssetAdmin


class PBSMMSpecialAdmin(PBSMMAbstractAdmin):
    model = PBSMMSpecial
    form = PBSMMSpecialEditForm
    add_form = PBSMMSpecialCreateForm
    list_filter = ('show__slug',)

    list_display = (
        'pk',
        'title_sortable',
        'show',
        'premiered_on',
        'date_last_api_update',
        'last_api_status_color',
        'show_publish_status')
    list_display_links = ('pk', 'title_sortable')
    # Why so many readonly_fields?  Because we don't want to override what's coming from the API, but we do
    # want to be able to view it in the context of the Django system.
    #
    # Most things here are fields, some are method output and some are
    # properties.
    readonly_fields = [
        'date_created', 'date_last_api_update', 'last_api_status', 'api_endpoint_link', 'last_api_status_color',
        'title', 'title_sortable',
        'description_long', 'description_short',
        'updated_at', 'premiered_on',
        'links',
        'language',
        'nola',

        'assemble_asset_table',
    ]

    # If we're adding a record - no sense in seeing all the things that aren't there yet, since only these TWO
    # fields are editable anyway...
    add_fieldsets = (
        (None, {'fields': ('slug', 'show'), }),
    )

    fieldsets = (
        (None, {
            'fields': (
                'ingest_on_save',
                ('date_created', 'date_last_api_update',
                 'updated_at', 'last_api_status_color'),
                'api_endpoint_link',
                'object_id',
            ),
        }),
        ('Title, Slug, Link', {  # 'classes': ('collapse in',),
            'fields': (
                'title', 'title_sortable', 'slug', 'api_endpoint_link', 'last_api_status_color'
            ),
        }),
        ('Assets', {'fields': ('assemble_asset_table',), }),
        ('Description and Texts', {'classes': ('collapse',),
                                   'fields': (
            'description_long', 'description_short',
            # 'funder_message'
        ),
        }),
        # ('Images', {'classes': ('collapse',),
        #    'fields': (
        #        'images', 'canonical_image_tag'
        #    )
        # }),
        ('Special Metadata', {'classes': ('collapse',),
                              'fields': (
            ('premiered_on', 'nola'),
            'language',
        ),
        }),
        ('Other', {'classes': ('collapse',),
                   'fields': (
            'links',
        ),
        }),
    )

    # Switch between the fieldsets depending on whether we're adding or
    # viewing a record
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


class PBSMMSpecialAssetAdmin(PBSMMAbstractAssetAdmin):
    model = PBSMMSpecialAsset
    list_display = ('pk', 'object_id', 'special_title', 'object_type', 'legacy_tp_media_id', 'asset_publicly_available',
                    'title_sortable', 'duration')

    def special_title(self, obj):
        return obj.special.title
    special_title.short_description = 'Special'


admin.site.register(PBSMMSpecial, PBSMMSpecialAdmin)
admin.site.register(PBSMMSpecialAsset, PBSMMSpecialAssetAdmin)
