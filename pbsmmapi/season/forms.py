from django.forms import ModelForm

from pbsmmapi.season.models import Season


class PBSMMSeasonCreateForm(ModelForm):
    """
    Override the Model form so that only these two fields show up.
    This is for adding a Season "by hand" although in general, they will
    be created as part of the process of seeding a Show.
    """

    class Meta:
        model = Season
        fields = ("object_id", "show")


class PBSMMSeasonEditForm(ModelForm):
    class Meta:
        model = Season
        exclude = []
