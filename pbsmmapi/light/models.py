from django.db import models
from .abstract_models import PBSMMLightGlobalAbstract, PBSMMLightObject

class PBSMMLightAsset(PBSMMLightObject):
    pass
    
class PBSMMLightCollection(PBSMMLightObject):
    pass
    
class PBSMMLightEpisode(PBSMMLightObject):
    pass
    
class PBSMMLightFranchise(PBSMMLightObject):
    pass
    
class PBSMMLightRemoteAsset(PBSMMLightObject):
    pass
    
class PBSMMLightSeason(PBSMMLightGlobalAbstract):
    pass
    
class PBSMMLightShow(PBSMMLightObject):
    pass
    
class PBSMMLightSpecial(PBSMMLightObject):
    pass
    
