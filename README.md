<div align="center">

<img src="gridwars-banner.png" alt="GridWars.run" width="800" />

### TRON-themed hosted MUD. Full PvP. No deletion. Free to play.

[![Status](https://img.shields.io/badge/status-pre--launch-orange?style=flat-square)]()
[![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-blue?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?style=flat-square)](pyproject.toml)
[![Engine](https://img.shields.io/badge/engine-Evennia_v6.0.0-green?style=flat-square)](vendor/evennia)
[![CI](https://github.com/jsgerman-oss/gridwars.run/actions/workflows/test.yml/badge.svg?style=flat-square)](.github/workflows/test.yml)

[Play](#quickstart) |
[Features](#features) |
[Development](#architecture-and-development) |
[Docs](#docs)

</div>

---

## What is GridWars.run

GridWars.run is a TRON-themed, hosted, online-only MUD where Users, Programs, and Daemons fight across a persistent cyber-grid. It is free to play, terminal-native, browser-friendly, and built around full PvP without character deletion or pay-to-win shortcuts: if you are derezzed, you respawn in Users' Sector with your identity intact, your faction still registered, and your disc progress preserved.

## Quickstart

Connect to the live Grid:

```bash
telnet game.gridwars.run 4000
```

Or open the web client:

<https://game.gridwars.run>

New players should start with the [Player Guide](docs/PLAYER.md). It covers account creation, first-session commands, faction choice, lightcycle duels, ratings, disc leveling, sector capture, and daemon PvE.

Useful first commands:

| Command | Purpose |
|---|---|
| `look` | Render the current sector. |
| `scan` | Tactical view: players, exits, faction control, local threats. |
| `status` | Identity Disc HUD: integrity, energy, XP, rank, faction, disc state. |
| `faction` | List factions and show your alignment. |
| `faction choose <name>` | Join Users, Programs, or Daemons. This is a one-shot choice. |
| `@queue duel` | Enter matchmaking for a rated lightcycle duel. |
| `@leaderboard` | Show the top-rated programs on the Grid. |

## Features

**Lightcycle duels.** Challenge a same-sector target with `challenge <target>` or enter open matchmaking with `@queue duel`. Accepted matches move both players into a private DuelArena. First to land three successful strikes wins; both players return to their pre-duel sector afterward.

**Matchmaking, ELO, and rewards.** The persistent matchmaking script pairs queued players automatically. Duel wins update ELO ratings, feed the public `@leaderboard`, award character XP, and grant equipped-disc XP through the post-duel reward hook.

**Identity discs.** Discs are equipment, not flavor text. `equip <disc>` slots one from your inventory, adds damage to `strike`, applies cooldowns, and tracks XP from combat. Discs level from 1 to 5, increasing their damage bonus as they grow.

**Factions.** Users, Programs, and Daemons have distinct lore, scan colors, combat messaging, and sector-control ambitions. Faction registration is persistent and intentionally hard to change.

**Ownership and capture.** `capture` claims the current sector for your faction. Control appears in `scan` and `status`, making the Grid's territorial state visible to everyone moving through it.

**Daemon PvE.** Daemon NPCs patrol, sense non-Daemon characters, strike with the same combat model as players, and respawn through scripted patrol and repop systems. They make the Grid hostile even when no players are waiting in-sector.

**42 generated zones.** Epic 19 added a seeded zone pipeline: eight archetypes expand into 42 deterministic, level-banded zones with generated rooms, exits, prose, spawn tables, and daemon palettes. Zone content is idempotent, so rebuilds skip existing rooms rather than duplicating the Grid.

**No character deletion.** Defeat derezzes and respawns; it does not delete. The core invariant is that a Character remains a Character. Mechanics that remove pressure should respawn, demote, debuff, exile, or move the player, never erase them.

## Architecture and Development

GridWars.run is an Evennia v6.0.0 game on Python 3.12+. Evennia is vendored under [vendor/evennia](vendor/evennia) and treated as read-only. All game-specific code lives in [gridwars](gridwars): commands, typeclasses, world systems, server settings, web assets, tests, and generated content hooks.

The main extension points are straightforward:

| Area | Path |
|---|---|
| Commands | [gridwars/commands](gridwars/commands) |
| Character, disc, daemon, exit typeclasses | [gridwars/typeclasses](gridwars/typeclasses) |
| Combat, duels, factions, ownership, matchmaking | [gridwars/world](gridwars/world) |
| Generated zone pipeline | [gridwars/world/zones](gridwars/world/zones) |
| Server configuration | [gridwars/server/conf](gridwars/server/conf) |

Local setup is for contributors testing changes before review:

```bash
git clone --recurse-submodules https://github.com/jsgerman-oss/gridwars.run.git
cd gridwars.run
make install
make migrate
make createsuperuser
make run
```

Then connect locally with `telnet localhost 4000` or open <http://localhost:4001>. Run `make test` before opening a pull request. CI runs the same test target on push and PR.

Two Evennia details matter in this codebase. First, `AttributeProperty` fields are read and written directly (`char.integrity`, `char.rating`, `disc.level`); do not use raw attribute lookups for normal gameplay state unless a specific typeclass edge case requires it. Second, settings paths are relative to the game directory, so typeclass paths look like `typeclasses.characters.Character`, not `gridwars.typeclasses.characters.Character`.

World construction is idempotent. Core sectors are tagged during `world.build_grid`, generated zones are tagged under the shared `world_build` category, and character spawn resolves by tag instead of a hard-coded dbref. That keeps rebuilds and migrations predictable while the hosted Grid evolves.

## Docs

| Guide | Purpose |
|---|---|
| [Player Guide](docs/PLAYER.md) | How to connect, survive, duel, level discs, and read the Grid. |
| [Hosting Guide](docs/HOSTING.md) | Cloudflare Pages deployment plus operator snippets for queue, ratings, discs, and arena cleanup. |
| [Zone Overview](docs/ZONES.md) | Player-facing overview of the generated zone set. |
| [World Content Runbook](docs/operations/world-content-runbook.md) | Operator runbook for generated world content. |
| [Contributing](CONTRIBUTING.md) | Branch policy, review workflow, and project conventions. |
| [Setup](docs/SETUP.md) | Local contributor setup and world build procedure. |
| [Conventions](docs/CONVENTIONS.md) | SPDX and source-file conventions. |

## License

GridWars.run game code is licensed [AGPL-3.0-or-later](LICENSE). Vendored Evennia retains its [BSD-3-Clause](vendor/evennia/LICENSE.txt) license. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution.

<sub>Built with <a href="https://www.evennia.com">Evennia</a>. Logo and theming &copy; 2026 Jay German.</sub>
