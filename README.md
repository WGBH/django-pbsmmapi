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
(`mm_content`) is marked with a `deleted` timestamp (taken from the changelog entry), and the mark
cascades to its descendants' records (seasons, episodes, specials, assets). The `ChangeLog` row
carries a mirror `deleted` timestamp so the state is recorded even when no local object exists.
Marked objects are excluded from all re-ingestion paths so they are neither re-fetched nor
resurrected. If a newer changelog entry shows the object was restored, the mark is cleared
automatically; the *Reingest selected items* admin action also clears it as an explicit override.

Restoring a parent only clears the marks its own deletion cascaded: an object deleted by its own
changelog entry stays deleted until its own restore (or the admin override). Repeated delete
entries do not advance the recorded deletion time — `deleted` always reflects the first time the
object disappeared. A model row whose `mm_content` is not linked cannot carry a mark; only the
changelog mirror records its state.

Rows are never deleted locally, so consuming projects should filter them out where appropriate:

```python
Show.objects.filter(mm_content__deleted__isnull=True)
```

After upgrading and running `migrate`, run the one-time (idempotent) backfill to apply delete
entries already recorded in the changelog table:

```bash
python manage.py backfill_deleted
```
