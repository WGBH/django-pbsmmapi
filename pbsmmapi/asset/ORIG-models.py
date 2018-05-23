from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..abstract.models import PBSMMLightObject

class PBSMMAbstractAsset(PBSMMLightObject):
    
    legacy_tp_media_id = models.BigIntegerField (
        _('COVE ID'),
        null = True, blank = True,
        unique = True, 
        help_text = '(Legacy TP Media ID)'
    )
    
    class Meta:
        abstract = True
        