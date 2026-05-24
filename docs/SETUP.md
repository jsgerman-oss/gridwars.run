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
installing Evennia is covered in Epic 2 (not yet written). Do not install
anything based on this file alone; this document covers only the clone step.
