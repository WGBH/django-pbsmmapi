from django.forms import ModelForm

from pbsmmapi.special.models import Special


class PBSMMSpecialCreateForm(ModelForm):
    class Meta:
        model = Special
        fields = ("slug", "show")


class PBSMMSpecialEditForm(ModelForm):
    class Meta:
        model = Special
        exclude = []
