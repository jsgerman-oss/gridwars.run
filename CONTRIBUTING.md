# Contributing to GridWars.run

GridWars.run is open source under AGPL-3.0-or-later. Issues, PRs, and design discussion are all welcome.

## Filing an issue

Two channels:

- **GitHub Issues** — for bug reports, feature requests, and design discussion from external contributors.
- **bd (beads)** — internal task graph used by the maintainers. The `.beads/` directory is committed; you can browse it, but you don't need `bd` installed to contribute.

When in doubt, file on GitHub Issues. The maintainers will mirror to bd if needed.

## PR workflow

```bash
git clone --recurse-submodules https://github.com/jsgerman-oss/gridwars.run.git
cd gridwars.run
git checkout -b your-branch-name
make install        # one-time: creates .venv and installs dependencies
# ... make your changes ...
make test           # MUST pass before opening the PR
git push -u origin your-branch-name
gh pr create
```

PRs run CI automatically. Green-on-CI is the bar for review.

## The absolute rule: don't touch `vendor/evennia/`

`vendor/evennia/` is a git submodule pinned to a specific Evennia release. Modifying anything inside it will either:

1. Be lost the next time the submodule is updated, or
2. Pollute the upstream contract reserved for clean releases.

If you need to change Evennia behavior, **extend** it from the `gridwars/` game directory — that is what Evennia is designed for. If you have found a real bug or missing feature in Evennia itself, file it upstream at <https://github.com/evennia/evennia>.

## Adding a new in-game command

The GridWars pattern:

1. Write the command class in `gridwars/commands/<your_command>.py`, subclassing `evennia.Command`. Set `key`, `aliases`, `locks`, and `help_category = "GridWars"` (so it shows up under `help gridwars`). Implement `func()`.
2. Import the class and register it in `gridwars/commands/default_cmdsets.py` — inside `CharacterCmdSet.at_cmdset_creation`, add `self.add(YourCommand())`.
3. Add tests under `gridwars/commands/tests/test_<your_command>.py` using `EvenniaCommandTest`.
4. (Optional) Update `gridwars/world/help_entries.py` if your command warrants top-level visibility in `help gridwars`.

## Working with Character stats

The `Character` typeclass (`gridwars/typeclasses/characters.py`) exposes `integrity`, `energy`, `experience`, `faction`, and `grid_rank` via Evennia `AttributeProperty`.

**Read and write them as direct attributes** — `c.integrity = 50`, not `c.attributes.get("integrity")`. The `.attributes` API bypasses the descriptor and silently returns `None`. (Yes, this bit us once.)

For mutations, prefer the helper methods (`take_damage`, `heal`, `gain_experience`, `reset_for_respawn`) — they clamp values correctly.

## Extending the world

`gridwars/world/build_grid.py` is the canonical sector builder. To add a sector:

1. Add an entry to the `SECTORS` dict (slug → `{key, desc}`).
2. Add the appropriate exits to the `EXITS` table.
3. Tag the new room with `("gridwars-core", "world_build")` for the idempotent rebuild.
4. Run via Django shell:

```bash
cd gridwars && ../.venv/bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from world import build_grid
"
```

## SPDX header convention

Every new GridWars source file should begin with:

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
```

Vendored Evennia files retain their original BSD-3-Clause headers — do not modify them.

Full convention reference: [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

## Style

- PEP 8.
- Type hints encouraged on public functions.
- No mock databases in tests — Evennia's `EvenniaTest` / `EvenniaCommandTest` give you a real DB per test run.
- Atomic commits; descriptive messages explaining *why*, not just what.
- One concern per PR. If you find a second thing while fixing the first, file a follow-up issue instead of expanding scope.

## The character-deletion rule

GridWars is full PvP, but **characters are never deleted** by any in-game action. Defeat sends the target back to Users' Sector with restored integrity. If you are adding a new combat or punishment mechanic, this rule is invariant: respawn, demote, debuff, exile — never delete.

## Questions

Open a GitHub Issue with the `question` label, or ping `@jsgerman-oss` on the relevant PR.
