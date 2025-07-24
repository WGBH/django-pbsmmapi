from django.contrib import admin
from django.contrib.admin import site
from django.utils.safestring import mark_safe

# This removed the delete function from the Admin action dropdown.
# You can 're-add' it, if necessary, by explicitly adding it to the
# actions parameter for a given ModelAdmin instance.
site.disable_action("delete_selected")


class PBSMMAbstractAdmin(admin.ModelAdmin):
    actions = [
        "force_reingest",
    ]
    search_fields = [
        "title",
    ]

    def force_reingest(self, request, queryset):
        # queryset is the list of Asset items that were selected.
        for item in queryset:
            item.ingest_on_save = True
            # HOW DO I FIND OUT IF THE save() was successful?
            item.save()

    force_reingest.short_description = "Reingest selected items."

    def assemble_asset_table(self, obj):
        asset_list = obj.assets.all()
        out = get_abstract_asset_table(asset_list)
        return mark_safe(out)

    assemble_asset_table.short_description = "Assets"

    class Meta:
        abstract = True


def get_abstract_asset_table(object_list):
    url = "/admin/asset/asset"
    if len(object_list) < 1:
        return "(No assets)"
    out = '<table width="100%" border=2>'
    out += (
        '\n<tr style="background-color:'
        ' #999;l"><th>Title</th><th>Type</th>'
        "<th>Duration</th><th>Avail?</th><th>API</th></tr>"
    )
    for item in object_list:
        row_color = "#ffffff;"

        out += '\n<tr style="background-color:%s">' % row_color
        out += '\n\t<td><a href="%s/%d/change/" target="_new">%s</a></td>' % (
            url,
            item.id,
            item.title,
        )
        out += "\n\t<td>%s</td>" % item.asset_type
        out += "\n\t<td>%s</td>" % item.formatted_duration
        out += "\n\t<td>%s</td>" % item.asset_publicly_available()
        out += '\n\t<td><a href="%s" target="_new">API</a></td>' % item.api_endpoint
        out += "\n</tr>"
    out += "\n</table>"
    return out
