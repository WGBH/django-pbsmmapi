from django.forms import ModelForm

from .models import PBSMMEpisode

class PBSMMEpisodeCreateForm(ModelForm):

    class Meta:
        model = PBSMMEpisode
        fields = (
            'object_id',
        )

class PBSMMEpisodeEditForm(ModelForm):

    class Meta:
        model = PBSMMEpisode
        exclude = []
