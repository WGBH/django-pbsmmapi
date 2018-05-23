from ..api.api import get_PBSMM_record
from ..api.helpers import check_pagination
from ..episode.models import PBSMMEpisode
from ..episode.ingest_episode import process_episode_record

def process_episodes(endpoint, this_season): 
    keep_going = True
    while keep_going:
        (status, json) = get_PBSMM_record(endpoint) # this is the "Seasons" endpoint for the show
    
        episode_list = json['data']
        page_links = json['links']
        
        for item in episode_list:
        
            attrs = item.get('attributes')
            links = item.get('links')
            object_id = item.get('id')
        
            try:
                instance = PBSMMEpisode.objects.get(object_id=object_id)
            except PBSMMEpisode.DoesNotExist:
                instance = PBSMMEpisode()
            
            instance = process_episode_record(item, instance)
            instance.season = this_season
            instance.ingest_on_save = True
                    
            instance.save()
            
        (keep_going, endpoint) = check_pagination(json)
    return

