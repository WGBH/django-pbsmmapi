from django import forms 
from .models import PBSMMEpisode

class PBSMMEpisodeCreateForm(forms.ModelForm):

    class Meta:
        model = PBSMMEpisode
        fields = ('object_id',)

class PBSMMEpisodeEditForm(forms.ModelForm):

    class Meta:
        model = PBSMMEpisode
        exclude = []
