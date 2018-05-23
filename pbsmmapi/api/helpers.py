
def check_pagination(json):
    if 'links' in json.keys():
        links = json['links']
        if 'next' in links.keys():
            if links['next'] is not None:
                return (True, links['next'])
    return (False, None)
    
    