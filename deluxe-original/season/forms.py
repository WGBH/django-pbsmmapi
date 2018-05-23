from django.forms import ModelForm

from .models import PBSMMSeason

class PBSMMSeasonCreateForm(ModelForm):

    class Meta:
        model = PBSMMSeason
        fields = (
            'object_id',
        )

class PBSMMSeasonEditForm(ModelForm):

    class Meta:
        model = PBSMMSeason
        exclude = []
