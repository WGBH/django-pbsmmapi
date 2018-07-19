from django.contrib import admin

from .models import PBSMMShow, PBSMMSeason, PBSMMSpecial, PBSMMEpisode
from ..episode.admin import PBSMMAbstractEpisodeAdmin, PBSMMEpisodeAssetAdmin
from ..episode.models import PBSMMEpisodeAsset
from ..season.admin import PBSMMAbstractSeasonAdmin, PBSMMSeasonAssetAdmin
from ..season.models import PBSMMSeasonAsset
from ..show.admin import PBSMMAbstractShowAdmin, PBSMMShowAssetAdmin
from ..show.models import PBSMMShowAsset
from ..special.admin import PBSMMAbstractSpecialAdmin, PBSMMSpecialAssetAdmin
from ..special.models import PBSMMSpecialAsset

class PBSMMShowAdmin(PBSMMAbstractShowAdmin):
    model = PBSMMShow
    
class PBSMMSpecialAdmin(PBSMMAbstractSpecialAdmin):
    model = PBSMMSpecial
    
class PBSMMEpisodeAdmin(PBSMMAbstractEpisodeAdmin):
    model = PBSMMEpisode
    
class PBSMMSeasonAdmin(PBSMMAbstractSeasonAdmin):
    model = PBSMMSeason
    

admin.site.register(PBSMMShow, PBSMMShowAdmin)
admin.site.register(PBSMMShowAsset, PBSMMShowAssetAdmin)
admin.site.register(PBSMMSeason, PBSMMSeasonAdmin)
admin.site.register(PBSMMSeasonAsset, PBSMMSeasonAssetAdmin)
admin.site.register(PBSMMSpecial, PBSMMSpecialAdmin)
admin.site.register(PBSMMSpecialAsset, PBSMMSpecialAssetAdmin)
admin.site.register(PBSMMEpisode, PBSMMEpisodeAdmin)
admin.site.register(PBSMMEpisodeAsset, PBSMMEpisodeAssetAdmin)
