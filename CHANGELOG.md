# Changelog

All notable changes to GridWars.run are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0] — 2026-05-24

**First playable slice.** GridWars.run boots end-to-end on Evennia v6.0.0 with five sectors, three factions, same-sector PvP, and 34 passing unit tests.

### Added
- Vendored Evennia v6.0.0 (BSD-3-Clause) under `vendor/evennia/` as a pinned git submodule
- AGPL-3.0-or-later license + `THIRD_PARTY_NOTICES.md` attributing Evennia
- 5 sectors with cyber-grid flavor: Users' Sector (spawn), Lightcycle Causeway, Daemon Gate, Archive Node, Combat Grid
- Idempotent world build script (`gridwars/world/build_grid.py`) with tag-based identity
- Character typeclass with `integrity` / `energy` / `experience` / `faction` / `grid_rank` (AttributeProperty) and clamping helpers
- Tag-based spawn resolution via `Account.create_character()` override — robust across world rebuilds
- 3-faction system (Users / Programs / Daemons) with `faction` and `faction choose <name>` commands + room broadcast
- `strike <target>` PvP command with deterministic + jitter damage, themed defeat flow, and tag-resolved respawn to Users' Sector. Characters are never deleted.
- `status` (Identity Disc HUD) and `scan` (tactical sector view with faction tinting)
- `help gridwars` curated command index
- Connection-screen banner + login/logout themed messages + faction-unaffiliated nudge
- 34 unit tests (real-DB via `EvenniaTest` / `EvenniaCommandTest`) across character, faction, status, scan, strike, world build
- GitHub Actions CI workflow on push + PR
- `make install / migrate / run / stop / test / createsuperuser` Makefile targets
- `docs/SETUP.md` setup procedure; `docs/CONVENTIONS.md` SPDX header rule
- README, CONTRIBUTING, AGENTS documentation
- Brand assets: `gridwars-banner.svg`, logo + favicon

### Notes
- Public server at gridwars.run is not yet deployed; players connect locally for now.
- 4 v0.2 epics filed in bd: Sector Ownership, Identity Discs, Daemon AI, Lightcycle Duels.

[v0.1.0]: https://github.com/jsgerman-oss/gridwars.run/releases/tag/v0.1.0
