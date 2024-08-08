# django-pbsmmapi
Code to model PBS MediaManager objects; scripts to ingest data into those models.

## Introduction

This is a Django app to allow Django-based projects to work with the PBS MediaManager API.
It is not expected to be a COMPLETE interface to the entirety of the PBS MediaManager; however
it should allow access to all of the primary content object types.

Documentation is in the "docs" directory.

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
        ]
```

2. Create your database.  *Be sure to support UTF-8 4-byte characters!*   In MySQL you can use:

```python
        CREATE DATABASE my_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. You'll need to change your settings DATABASES accordingly:

```python
        DATABASES = {
                'default': {
                        'ENGINE': 'django.db.backends.mysql',
                        'HOST': '',
                        'NAME': 'my_database',
                        'OPTIONS': {
                                'read_default_file': '~/.my.cnf',
                                'charset': 'utf8mb4',
                        }
                }
        }
```

4. You ALSO need to have PBS Media Manager credentials - an API KEY and a SECRET KEY.  These also go into the base settings.py file of your project:

```python
        PBSMM_API_ID='abcdefghijklmnop'
        PBSMM_API_SECRET= 'aAbBcCdDeEfFgGhHjJkKmMnNpPqQrRsS'
```

## How it all works:

### Data Ingestion

You ingest objects from PBS Media Manager by going to the Admin page for the object type.  Objects that have children can optionally import their children at the same time.

A good place to start is with the Show Admin page. (`/admin/show/pbsmmshow/add/`).

    * If you enter the slug and click "Save" it will ingest that Show's record and nothing more.
    * If you click "Ingest Seasons" and then "Save" it will ingest the Show, **and** any Season records associated with it.
    * Ditto for "Ingest Specials".
    * To use "Ingest Episodes", you also have to select "Ingest Seasons".

### Each object has two parameters that control public access to it:

1. The `publish_status` flag which can take 3 different values:

    | Value | Description |
    |  ---  | --- |
    | -1 | GLOBALLY OFFLINE - unavailable to anyone (public, admins) |
    | 0 | PROVISIONAL - availability depends on `live_as_of` value  |
    | 1 | PERMANENTLY LIVE - available to everyone |

2. The `live_as_of` time stamp.

    * The default (upon object creation) is NULL, which indicates a "never published" status.
    * If the Admin sets the date in the future, it is unavailable to the public UNTIL the `live_as_of` date/time is reached;
    * If the date is set in the past, the page is "live".
    * NOTE THAT the "PERMANENTLY LIVE" and "GLOBALLY OFFLINE" `publish_status` settings OVERRIDE this behavior.

Admins can access every record on the site EXCEPT those whose publish_status is "GLOBALLY OFFLINE"

## Additional Management

On each object's Admin listing page, there are several "bulk actions" available to you:

| Action | `publish_status` | `live_as_of` date | Description |
| --- | --- | --- | --- |
| Reingest Selected Items | (same) | (same) | This essentially "updates" the record from PBSMM.  No status change is made. |
| Take Item PERMANENTLY LIVE | 1 | (same) | Item "goes live", `live_as_of` date is ignored. |
| Take Live as of Right Now | 0 | "now" | Item "goes live" by resetting `live_as_of` to "right now". |
| CONDITIONALLY Online Using `live_as_of` Date | 0 | (same) | Item will go live automatically as of the `live_as_of` date. |
| Take Item COMPLETELY OFFLINE | -1 | (same) | Item is taken off of the site. |


## Using PBSMMAPI as part of your Django project

Once you have everything installed and the database migrated, you can start to ingest content.

In order to build your site, you have to - at the least - create templates for each object's listing page and detail page:

    * `show/show_detail.html` and `show/show_list.html`
    * `season/season_detail.html` and `season/season_list.html`
    * `special/special_detail.html` and `special/special_list.html`
    * `episode/episode.detail.html` and `episode/episode_list.html`

There are "default" skeleton templates build into `django-pbsmm` which will show up if Django can't find your project's templates, but they are definitely not usable for a production environment.
