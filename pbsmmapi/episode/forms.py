from django import forms 
from ..custom.select_model import find_PBSMM_model

PBSMMEpisode = find_PBSMM_model('CUSTOM_PBSMM_EPISODE_MODEL')

class PBSMMEpisodeCreateForm(forms.ModelForm):
    """
    This overrides the Admin form when creating an Episode (by hand).
    Usually Episodes are "created" when ingesting a parental Season
    (or a grand-parental Show).
    """
    class Meta:
        model = PBSMMEpisode
        fields = ('slug', 'season')

class PBSMMEpisodeEditForm(forms.ModelForm):

    class Meta:
        model = PBSMMEpisode
        exclude = []
