from django import forms

from pbsmmapi.episode.models import Episode


class PBSMMEpisodeCreateForm(forms.ModelForm):
    """
    This overrides the Admin form when creating an Episode (by hand).
    Usually Episodes are "created" when ingesting a parental Season
    (or a grand-parental Show).
    """

    class Meta:
        model = Episode
        fields = ("slug", "season")


class PBSMMEpisodeEditForm(forms.ModelForm):
    class Meta:
        model = Episode
        exclude = []
