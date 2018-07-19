from django.apps import apps
from django.conf import settings
from django.db import models

class EmptyAbstractModel(models.Model):
    pass
    
    class Meta:
        abstract = True

def custom_abstract_fields(this_setting):
    """
    Return the native or custom model depending on whether there's a tuple set for a PBSMM Model setting, e.g.:
    CUSTOM_PBSMM_EPISODE_MODEL = ('pbsmm', 'PBSMMEpisode')
    """
    if hasattr(settings, this_setting):        
        (app_name, model_name) = getattr(settings, this_setting)
        
        try:    
           return apps.get_model(app_name, model_name, require_ready=True)
        except:
            pass
            
    return EmptyAbstractModel
        
