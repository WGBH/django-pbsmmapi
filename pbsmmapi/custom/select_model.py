from django.apps import apps
from django.conf import settings

native_models = {
    'show': ('native','PBSMMShow'), 
    'special': ('native', 'PBSMMSpecial'), 
    'episode': ('native', 'PBSMMEpisode'),
    'special': ('native', 'PBSMMSpecial'), 
}

def find_PBSMM_model(this_setting):
    """
    Return the native or custom model depending on whether there's a tuple set for a PBSMM Model setting, e.g.:
    CUSTOM_PBSMM_EPISODE_MODEL = ('pbsmm', 'PBSMMEpisode')
    
    """
    if hasattr(settings, this_setting):        
        (app_name, model_name) = getattr(settings, this_setting)

    else:
        foo = settings.this_setting.split('_')[2].lower()
        if foo and foo in native_models.keys():
            (app_name, model_name) = native_models[foo]
        else:
            return None
    
    try:    
       #return apps.get_model(app_name, model_name, require_ready=True)
       return apps.get_model(app_name, model_name, require_ready=False)
    except:
        return None