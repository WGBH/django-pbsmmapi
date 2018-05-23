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

        INSTALLED_APPS = [
                ...
                'pbsmmapi.episode',
                'pbsmmapi.season',
                'pbsmmapi.show',
                'pbsmmapi.special',
        ]
        
2. Create your database.  _Be sure to support UTF-8 4-byte characters!_   In MySQL you can use:

    `CREATE DATABASE my_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
    
3. You'll need to change your settings DATABASES accordingly:

    ```
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

    ```
    PBSMM_API_ID='abcdefghijklmnop'
    PBSMM_API_SECRET= 'aAbBcCdDeEfFgGhHjJkKmMnNpPqQrRsS'
    ```
    


