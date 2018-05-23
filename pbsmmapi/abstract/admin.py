from django.contrib import admin
from django.contrib.admin import site
from django.utils.safestring import mark_safe

# This removed the delete function from the Admin action dropdown.
# You can 're-add' it, if necessary, by explicitly adding it to the actions parameter for a given ModelAdmin instance.
site.disable_action('delete_selected')

class PBSMMAbstractAdmin(admin.ModelAdmin):
    actions = ['force_reingest', 'make_publicly_available','take_offline']
    search_fields = ['title',]
    def force_reingest(self, request, queryset):
        # queryset is the list of Asset items that were selected.
        for item in queryset:
            item.ingest_on_save = True
            # HOW DO I FIND OUT IF THE save() was successful?
            item.save()
    force_reingest.short_description = 'Reingest selected items.'
    
    def make_publicly_available(self, request, queryset):
        for item in queryset:
            item.publish_status = 1
            item.save()
    make_publicly_available.short_description = 'Take item LIVE (to the public)'
            
    def take_offline(self, request, queryset):
        for item in queryset:
            item.publish_status = 0
            item.save() 
    take_offline.short_description = 'Take item OFFLINE (admin only)'
    
    def assemble_asset_table(self, obj):
        asset_list = obj.assets.all()
        out = get_abstract_asset_table(asset_list, obj.default_asset, obj.object_model_type)
        return mark_safe(out)
    assemble_asset_table.short_description = 'Assets'
    
    class Meta:
        abstract = True
    
def get_abstract_asset_table(object_list, default_asset, parent_type):
    url = '/admin/%s/pbsmm%sasset' % (parent_type, parent_type)
    if len(object_list) < 1:
        return "(No assets)"
    out = "<p>Red asterisk indicates which Asset will appear on the parent object's detail page.</p>"
    out += "<table width=\"100%\" border=2>"
    out += "\n<tr><th>Title</th><th>Type</th><th>Duration</th><th>Avail?</th><th>API</th><th>Set as Default?</th></tr>"
    for item in object_list:
        default_mark = '&nbsp;&nbsp;'
        if default_asset is not None and item == default_asset:
            default_mark = '<span style=\"color: #f00;\">*</span>&nbsp;'

        out += "\n<tr>"
        out += "\n\t<td>%s<a href=\"%s/%d/change/\" target=\"_new\">%s</a></td>" % (default_mark, url, item.id, item.title)
        out += "\n\t<td>%s</td>" % item.object_type
        out += '\n\t<td>%s</td>' % item.formatted_duration
        out += "\n\t<td>%s</td>" % item.asset_publicly_available()
        #out += "\n\t<td>%s%s</td>" % (item.asset_publicly_available(), default_mark)
        out += "\n\t<td><a href=\"%s\" target=\"_new\">API</a></td>" % item.api_endpoint
        out += "\n\t<td>%s</td>" % item.is_default
        out += "\n</tr>"
    out += "\n</table>"
    return out