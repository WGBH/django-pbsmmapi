from django.db import models
from django.db.models import Q
import datetime

class PBSMMObjectManager(models.Manager):
    
    def get_queryset(self, user):
        if user.is_authenticated:
            return super(PBSMMObjectManager, self).get_queryset()
            
        qs = super(PBSMMObjectManager, self).get_queryset().exclude(publish_status__lt=0)
        # 
        # Also exclude those with publish_status = 0 and date < now.
        #
        now = datetime.datetime.now()
        qs = qs.exclude (
            Q (publish_status=0)
            & Q(live_as_of__date__gte=now)
        )