# SPDX-License-Identifier: AGPL-3.0-or-later
# GridWars.run — Setup

## Cloning GridWars.run

Always clone with `--recurse-submodules` to populate the Evennia vendor tree:

```bash
git clone --recurse-submodules https://github.com/jsgerman-oss/gridwars.run.git
cd gridwars.run
```

Verify the submodule is at the pinned commit (no `+`, `-`, or `U` prefix):

```bash
git submodule status
# expected:  966301fc1f0318224f7c78c3702131126075429b vendor/evennia (v6.0.0)
```

## Updating an existing clone

```bash
git pull
git submodule update --init --recursive
```

## If you forgot `--recurse-submodules`

Run the submodule init/update manually — it is safe to run at any time:

```bash
git submodule update --init --recursive
```

## Python version requirement

Python **3.12 or later** is required. Bootstrapping the game server and
installing Evennia is covered in the next section.

## Running GridWars.run locally

GridWars.run runs on Evennia v6.0.0 (Python 3.12+). After cloning the repo (see "Cloning" above):

```bash
make install     # creates .venv/, installs vendored Evennia (one-time + on dep updates)
make migrate     # initialise the SQLite DB (one-time; will prompt for superuser)
make run         # start the server
```

Connect:
- Telnet: `telnet localhost 4000`
- Webclient: open <http://localhost:4001> in any browser

Stop with `make stop`. Run the Evennia test harness with `make test`.

### Updating after a `git pull`

```bash
git submodule update --init --recursive   # sync vendored Evennia to the new pin
make install                              # re-resolves pip deps if Evennia bumped
make migrate                              # apply any new Django/Evennia migrations
```

### First-run superuser

`make migrate` applies all database migrations non-interactively. After migrating, run:

```bash
make createsuperuser
```

This account is the in-game `#1` character and the web-admin admin. Use a throwaway password for local dev.

## Building the grid

After `make install` and `make migrate`, populate the world with the five GridWars sectors:

```bash
cd gridwars && ../.venv/bin/python -c "import os, django; \
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings'); \
  django.setup(); from world import build_grid; build_grid.build()"
```

The script is idempotent — re-running it does NOT duplicate rooms (each is tagged `("gridwars-core", "world_build")` and reused if present). Fresh characters spawn in **Users' Sector** automatically via a tag-based `Account.create_character()` hook (gridwars/typeclasses/accounts.py).

### Sectors and exits

| Sector | Connects to |
|---|---|
| **Users' Sector** (spawn) | north -> Lightcycle Causeway, east -> Archive Node |
| **Lightcycle Causeway** | south -> Users' Sector, east -> Daemon Gate |
| **Daemon Gate** | west -> Lightcycle Causeway, north -> Combat Grid |
| **Archive Node** | west -> Users' Sector |
| **Combat Grid** | south -> Daemon Gate |
