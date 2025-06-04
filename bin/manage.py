#!/usr/bin/env python3
import os
import re
import sys

from django.core.management import execute_from_command_line
from testcontainers.compose import DockerCompose


def compose_running() -> bool:
    containers = DockerCompose(
        ".",
        compose_file_name="docker-compose.yml",
    ).get_containers()
    return bool(containers)


def env_vars_configured():
    required_env_vars = [
        "PGUSER",
        "PGPASSWORD",
        "PGDATABASE",
        "PGPORT",
        "PGHOST",
        "DJANGO_SETTINGS_MODULE",
        "PBSMM_API_ID",
        "PBSMM_API_SECRET",
    ]
    for env_var in required_env_vars:
        if env_var not in os.environ:
            print(f"Required environment variable {env_var} is unset")
            sys.exit()


if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    env_vars_configured()

    if compose_running():
        sys.exit(execute_from_command_line())
    else:
        with DockerCompose(
            ".",
            compose_file_name="docker-compose.yml",
            pull=True,
        ) as compose:
            stdout, stderr = compose.get_logs()
            sys.exit(execute_from_command_line())
