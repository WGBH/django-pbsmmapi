# django-pbsmmapi
Code to model PBS MediaManager objects; scripts to ingest data into those models.
========
PBSMMAPI
========

This is a Django app to allow Django-based projects to work with the PBS MediaManager API.
It is not expected to be a COMPLETE interface to the entirety of the PBS MediaManager; however
it should allow access to all of the primary content object types.

Documentation is in the "docs" directory.

Quick start
-----------

1. Add the pbsmmapi apps to your INSTALLED_APPS setting:

.. code-block:: python
        INSTALLED_APPS = [
                ...
                'pbsmmapi',
                'pbsmmapi.episode',
                'pbsmmapi.season',
                'pbsmmapi.show',
                'pbsmmapi.special',
        ]
        
2. Create your database.  *Be sure to support UTF-8 4-byte characters!*   In MySQL you can use:

.. code-block:: python
        CREATE DATABASE my_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    
3. You'll need to change your settings DATABASES accordingly:

.. code-block:: python
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

4. You ALSO need to have PBS Media Manager credentials - an API KEY and a SECRET KEY.  These also go into the base settings.py file of your project:

.. code-block:: python
        PBSMM_API_ID='abcdefghijklmnop'
        PBSMM_API_SECRET= 'aAbBcCdDeEfFgGhHjJkKmMnNpPqQrRsS'
    
5. How it all works:

5.1. Data ingestion

* You ingest objects from PBS Media Manager by going to the Admin page for the object type.  Objects that have children can optionally import their children at the same time.

5.2. Each object has two parameters that control public access to it:

        1. The ``publish_status`` flag which can take 3 different values:

        +------+----------------------------------------------------------------+
        |  -1  | GLOBALLY OFFLINE - unavailable to anyone (public, admins)      |
        +------+----------------------------------------------------------------+
        |   0  | PROVISIONAL - availability depends on ``live_as_of`` value     |
        +------+----------------------------------------------------------------+
        |   1  | PERMANENTLY LIVE - available to everyone                       |
        +------+----------------------------------------------------------------+

        2. The ``live_as_of`` time stamp.

        * The default (upon object creation) is NULL, which indicates a "never published" status.
        * If the Admin sets the date in the future, it is unavailable to the public UNTIL the ``live_as_of`` date/time is reached;
        * If the date is set in the past, the page is "live".
        * NOTE THAT the "PERMANENTLY LIVE" and "GLOBALLY OFFLINE" ``publish_status`` settings OVERRIDE this behavior.

Admins can access every record on the site EXCEPT those whose publish_status is "GLOBALLY OFFLINE"


