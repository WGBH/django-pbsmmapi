# django-pbsmmapi

Code to model PBS MediaManager objects; scripts to ingest data into those models.

## Introduction

This is a Django app to allow Django-based projects to work with the PBS MediaManager API. It is not expected to be a COMPLETE interface to the entirety of the PBS MediaManager; however it should allow access to all of the primary content object types.

In addition to Django, [huey](https://huey.readthedocs.io/en/latest/) is used for running background ingestion tasks.

## Quick start

1. Add the pbsmmapi apps to your INSTALLED_APPS setting:

```python
    INSTALLED_APPS = [
        ...
        'pbsmmapi',
        'pbsmmapi.episode',
        'pbsmmapi.season',
        'pbsmmapi.show',
        'pbsmmapi.special',
        'pbsmmapi.franchise',
        'pbsmmapi.changelog',
    ]
```

2. You ALSO need to have PBS Media Manager credentials - an API KEY and a SECRET KEY. These also go into the `settings.py` file of your project:

```python
    PBSMM_API_ID = os.environ["PBSMM_API_ID"]
    PBSMM_API_SECRET = os.environ["PBSMM_API_SECRET"]
```

It's not a good idea to commit these in plain text. Set them as environment variables (as suggested above) or using some other secret management tool.

3. To ingest shows and/or franchises automatically, configure `PBSMM_SHOW_SLUGS` and/or `PBSMM_FRANCHISE_SLUGS`:

```
PBSMM_SHOW_SLUGS = [
    "antiques-roadshow",
]

PBSMM_FRANCHISE_SLUGS = [
    "masterpiece",
]
```

Huey will attempt to scrape all Show and/or Franchise data, including Specials, Seasons, Episodes, and Assets. The changelog endpoint will also be scraped.

Once a complete ingest has finished, changelog data is used to ingest updated and newly added objects.

## Deleted objects

When the changelog reports an object as deleted, its row is kept but its `ContentRecord`
(`mm_content`) is marked with a `deleted` timestamp (taken from the changelog entry). The mark
also stamps the records of the object's **directly-attached assets** — the only descendants that
disappear silently: Media Manager requires children to be deleted before their parents, so every
franchise/show/season/episode/special gets its own changelog delete entry (which stamps its own
assets in turn), while a parent's assets never get entries of their own.

Marked objects are excluded from every ingestion path — the scrapers, the changelog API fetches
and the reingest-on-update pass all skip them, and `save()` will not fetch for them — so they are
neither re-fetched nor resurrected.

A delete is terminal. Recreating an object in the Media Manager Console produces a new content ID
(ingested here as a brand-new object), and unpublishing arrives as an `update` action, so a delete
entry is never superseded on the same content ID and there is no un-delete: the *Reingest selected
items* admin action simply skips deleted objects. For the same reason an asset that drops out of
its parent's asset list is left untouched on reingest — if it was really deleted, its own changelog
delete entry marks it.

Rows are never deleted locally, so consuming projects should filter them out where appropriate:

```python
Show.objects.filter(mm_content__deleted__isnull=True)
```

Delete entries already recorded in the changelog table are applied automatically by a one-time
(idempotent) data migration when you run `migrate` after upgrading.
