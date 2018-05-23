from django import forms 
from .models import PBSMMEpisode

class PBSMMEpisodeCreateForm(forms.ModelForm):

    class Meta:
        model = PBSMMEpisode
        fields = ('slug', 'season')

class PBSMMEpisodeEditForm(forms.ModelForm):

    class Meta:
        model = PBSMMEpisode
        exclude = []
