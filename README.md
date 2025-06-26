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
