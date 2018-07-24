from django.conf import settings
from django.db import models
from importlib import import_module

class EmptyAbstractModel(models.Model):
    pass
    
    class Meta:
        abstract = True

def custom_abstract_fields(this_setting):
    """
    Return the native or custom model depending on whether there's a tuple set for a PBSMM Model setting, e.g.:
    CUSTOM_PBSMM_EPISODE_MODEL 
    """
    if hasattr(settings, this_setting):        
        pieces = getattr(settings, this_setting).split('.')
        model_str = pieces.pop()
        module_str = '.'.join(pieces)
        module = import_module(module_str)
        model = getattr(module, model_str)
        return model
            
    else:
        return EmptyAbstractModel
