import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-pbsmmapi',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License, see LICENSE',  # example license
    description="Django models that import content from the PBS MediaManager API",
    long_description=README,
    url='http://github.com/wgbh/django-pbsmmapi/',
    author='Bob Donahue',
    author_email='bob_donahue@wgbh.org',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # example license
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.4',
        #'Programming Language :: Python :: 3.5',
        #'Topic :: Internet :: WWW/HTTP',
        #'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
