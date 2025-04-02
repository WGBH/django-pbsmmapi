def check_pagination(json):
    """
    This take the data from a PBSMM API returned record and looks to see if
    there is more content on additional pages.

    Since there's no way to override pagination from the endpoint URL (PBS
    being PBS), in order to get all of the objects in a complete list you have
    to scrape things page by page.

    This helper function just returns True or False as to whether there's still
    a "next" page or not.

    It's used in all of the ingest methods (since thankfully, the JSON
    structure is the same for all object types with regards to pagination).
    """
    if "links" in json.keys():
        links = json["links"]
        if "next" in links.keys():
            if links["next"] is not None:
                return (True, links["next"])
    return (False, None)
