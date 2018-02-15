from django import forms 
from .models import PBSMMEpisode

class PBSMMEpisodeCreateForm(forms.ModelForm):

    #ingest_related_assets = forms.BooleanField ( initial=False, required=False )

    class Meta:
        model = PBSMMEpisode
        fields = (
            'object_id', 'ingest_related_assets'
        )

class PBSMMEpisodeEditForm(forms.ModelForm):

    #ingest_related_assets = forms.BooleanField ( initial=False, required=False )

    class Meta:
        model = PBSMMEpisode
        exclude = []
