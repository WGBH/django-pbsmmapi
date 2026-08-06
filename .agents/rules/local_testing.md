---
description: Environment configuration, test container behavior, and execution rules for running tests and manage.py commands
trigger: model_decision
---

# Local Testing & Management Rules

## Overview

This project uses a custom `manage.py` script located at `./bin/manage.py` (not the project root). Human developers rely on `direnv` and `.envrc` to manage environment variables and Python virtual environments with `uv`.

When executing commands as an AI agent, `direnv` is not automatically evaluated in shell sessions. You must explicitly configure the required environment variables and use `uv run` when running tests or management commands.

---

## Required Environment Variables

`./bin/manage.py` strictly checks for 8 required environment variables upon execution and will abort if any are missing.

Always set or export the following variables prior to executing `./bin/manage.py`:

| Environment Variable | Recommended Value | Notes |
| :--- | :--- | :--- |
| `PGUSER` | `pbsmmapi` | Postgres username |
| `PGPASSWORD` | `pbsmmapi` | Postgres password |
| `PGDATABASE` | `pbsmmapi` | Postgres database name |
| `PGPORT` | `55432` | Host port mapped to Postgres container port `5432` |
| `PGHOST` | `localhost` | Database host |
| `DJANGO_SETTINGS_MODULE` | `pbsmmapi.test.settings` | Django test settings module |
| `PBSMM_API_ID` | `test` | Dummy value acceptable for unit tests (API requests are mocked) |
| `PBSMM_API_SECRET` | `test` | Dummy value acceptable for unit tests (API requests are mocked) |

---

## Containers & Sandbox Bypassing

- **Testcontainers & Docker Compose:** `./bin/manage.py` uses `testcontainers` to check if Docker containers (PostgreSQL and Valkey/Redis) defined in `docker-compose.yml` are running, and automatically spins them up if they are down.
- **Sandbox Requirement:** Interacting with Docker sockets and `uv` binaries outside the immediate workspace requires running shell commands with `BypassSandbox: true`.

---

## Standard Execution Commands

### Run Full Test Suite

```bash
export PGUSER=pbsmmapi
export PGPASSWORD=pbsmmapi
export PGDATABASE=pbsmmapi
export PGPORT=55432
export PGHOST=localhost
export DJANGO_SETTINGS_MODULE=pbsmmapi.test.settings
export PBSMM_API_ID=test
export PBSMM_API_SECRET=test

uv run python ./bin/manage.py test --noinput
```

### Run Specific Test Modules

```bash
export PGUSER=pbsmmapi PGPASSWORD=pbsmmapi PGDATABASE=pbsmmapi PGPORT=55432 PGHOST=localhost DJANGO_SETTINGS_MODULE=pbsmmapi.test.settings PBSMM_API_ID=test PBSMM_API_SECRET=test

uv run python ./bin/manage.py test pbsmmapi.show --noinput
```

### Other Management Commands

To run other Django management commands (e.g., `makemigrations`, `shell`), use the same environment export pattern:

```bash
uv run python ./bin/manage.py <command>
```
