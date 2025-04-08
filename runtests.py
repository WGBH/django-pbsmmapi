#!/usr/bin/env python

import os
import sys

from django.core.management import execute_from_command_line

os.environ["DJANGO_SETTINGS_MODULE"] = "pbsmmapi.test.settings"

if __name__ == "__main__":
    execute_from_command_line([sys.argv[0], "test"])
