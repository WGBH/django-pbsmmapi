#from pbsmmapi.asset.models import PBSMMAsset
from .models import PBSMMAsset

def ingest_related_asset(asset_id):
    
    try:
        asset = PBSMMAsset.objects.get(object_id = asset_id)
        op = 'update'
        
    except PBSMMAsset.DoesNotExist:
        asset = PBSMMAsset()
        asset.object_id = asset_id
        op = 'new'
        
    try:
        asset.ingest_on_save = True
        asset.save()
        return (op, asset.id)
    except:
        return (op, None)