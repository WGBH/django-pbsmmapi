from django.apps import apps
from django.conf import settings

from ..native.models import PBSMMShow as NativePBSMMShow, \
    PBSMMSpecial as NativePBSMMSpecial, \
    PBSMMEpisode as NativePBSMMEpisode, \
    PBSMMSeason as NativePBSMMSeason

native_models = {
    'show': NativePBSMMShow, 
    'special': NativePBSMMSpecial, 
    'episode': NativePBSMMEpisode, 
    'special': NativePBSMMSpecial 
}

def find_PBSMM_model(this_setting):
    """
    Return the native or custom model depending on whether there's a tuple set for a PBSMM Model setting, e.g.:
    CUSTOM_PBSMM_EPISODE_MODEL = ('pbsmm', 'PBSMMEpisode')
    
    """
    if settings.this_setting:        
        (app_name, model_name) = this_setting
        try:
            return apps.get_model(app_name, model_name)
        except:
            return None
    else:
        foo = settings.this_setting.split('_')[2].lower()
        if foo and foo in native_models.keys():
            return native_models[foo]
    return None