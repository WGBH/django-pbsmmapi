from django.contrib import admin
from django.contrib.admin import site
from django.utils.safestring import mark_safe

# This removed the delete function from the Admin action dropdown.
# You can 're-add' it, if necessary, by explicitly adding it to the
# actions parameter for a given ModelAdmin instance.
site.disable_action("delete_selected")


class AnnotatedReadonlyAdminMixin:
    """
    Surface queryset annotations as read-only values in the admin detail page.

    The model metadata now lives in ``mm_content.api_data`` and is exposed only
    as queryset annotations, not as model attributes. Naming an annotation in
    ``fieldsets`` therefore makes the change-form ``ModelForm`` raise
    ``FieldError``. For each name in ``annotated_fields`` we attach a display
    callable (an instance attribute, so ``hasattr(model_admin, name)`` passes
    the admin system checks and ``lookup_field`` renders the value) and force
    the name read-only on the edit form.
    """

    annotated_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.annotated_fields:
            if name not in self.__dict__:
                self.__dict__[name] = self._annotated_display(name)

    @staticmethod
    def _annotated_display(name):
        def display(obj):
            return getattr(obj, name, None)

        display.short_description = name.replace("_", " ").title()
        return display

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # Annotations are never editable form fields (they are derived from
        # api_data), so always force them read-only. On the add form they
        # simply render empty.
        readonly += [n for n in self.annotated_fields if n not in readonly]
        return readonly


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
