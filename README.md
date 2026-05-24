<p align="center">
  <img src="gridwars-banner.svg" alt="GridWars.run" width="800">
</p>

<h1 align="center">GridWars.run</h1>
<p align="center">
  <strong>Full PvP. No limits. Free to play. Open source.</strong>
</p>
<p align="center">
  <a href="https://github.com/jsgerman-oss/gridwars.run/actions/workflows/test.yml"><img src="https://github.com/jsgerman-oss/gridwars.run/actions/workflows/test.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg" alt="License: AGPL-3.0-or-later"></a>
</p>

---

GridWars.run is an open-source, text-based PvP world built for the Grid — five sectors spanning Users' Sector, Lightcycle Causeway, Daemon Gate, Archive Node, and Combat Grid. Pick your allegiance: **Users**, **Programs**, or **Daemons**. Traverse the causeway. Breach the gate. Derez rival programs in the Combat Grid. No pay-to-win. No deletion. Every character respawns.

Built on a vendored [Evennia](https://www.evennia.com) v6.0.0 engine; written in Python 3.12+; licensed AGPL-3.0-or-later.

## Get on the Grid

```bash
git clone --recurse-submodules https://github.com/jsgerman-oss/gridwars.run.git
cd gridwars.run
make install        # creates .venv/, installs vendored Evennia
make migrate        # initialize the SQLite DB (one-time)
make createsuperuser    # interactive — your in-game #1 character
make run            # boot the server
```

Then connect:

- Telnet: `telnet localhost 4000`
- Webclient: <http://localhost:4001>

Full setup details — including update-after-pull and the world-build step — live in [`docs/SETUP.md`](docs/SETUP.md).

## First playable slice

Once you're connected and have chosen a faction (`faction choose Users` / `Programs` / `Daemons`):

| Command | What it does |
|---|---|
| `status` | Identity disc HUD — integrity, energy, exp, rank, faction |
| `scan` | Tactical sector view — other programs (faction-tinted), exits, flavor |
| `faction` | List the three factions and your current alignment |
| `faction choose <name>` | Align with a faction (one-shot; admin override required to change) |
| `strike <target>` | Same-sector PvP. Defeat sends the target back to Users' Sector with restored integrity. No deletion, ever. |
| `help gridwars` | Curated command index by category |

## What's vendored

[Evennia](https://www.evennia.com) v6.0.0 lives under `vendor/evennia/` as a git submodule pinned to commit [`966301fc`](https://github.com/evennia/evennia/commit/966301fc1f0318224f7c78c3702131126075429b). Evennia provides networking, sessions, the web client, typeclasses, and the database layer. GridWars extends it via the `gridwars/` game directory; the vendored source is never modified. Attribution: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## License

GridWars.run code is licensed [AGPL-3.0-or-later](LICENSE). Vendored Evennia retains its [BSD-3-Clause](vendor/evennia/LICENSE.txt) license.

## Roadmap (sketch — non-binding)

- **Lightcycle duels** — instanced PvP races in the Causeway
- **Daemon AI** — autonomous corrupted processes patrolling sector borders
- **Sector ownership** — faction-controlled zones with permission semantics
- **Identity discs** — wieldable weapons with cooldowns and modifiers

Contributions welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) (or [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) for the SPDX header rule) before opening a PR.

---

<sub>Built with <a href="https://www.evennia.com">Evennia</a>. Logo / theming &copy; 2026 Jay German.</sub>
