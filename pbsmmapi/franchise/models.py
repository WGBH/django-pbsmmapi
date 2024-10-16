from django.db import models
from django.utils.translation import gettext_lazy as _

from pbsmmapi.abstract.models import PBSMMGenericFranchise


class Franchise(PBSMMGenericFranchise):
    ingest_shows = models.BooleanField(
        _("Ingest Shows"),
        default=False,
        help_text="Also ingest all Shows",
    )

    @property
    def object_model_type(self):
        # This handles the correspondence to the "type" field in the PBSMM JSON
        # object
        return "franchise"
