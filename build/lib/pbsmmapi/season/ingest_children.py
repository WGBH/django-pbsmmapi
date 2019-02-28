from ..api.api import get_PBSMM_record
from ..api.helpers import check_pagination
from ..episode.models import PBSMMEpisode
from ..episode.ingest_episode import process_episode_record


def process_episodes(endpoint, this_season):
    """
    Step through each page of a list of PBSMM API Episodes, and ingest each episode.

    As Episodes are always associated with a Season, that's the only parameter.
    """
    if this_season is None:  # oops no season - escape doing nothing...
        return

    keep_going = True
    while keep_going:
        # this is the "Seasons" endpoint for the show
        (status, json) = get_PBSMM_record(endpoint)

        episode_list = json['data']

        for item in episode_list:
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
