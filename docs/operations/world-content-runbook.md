# World Content Runbook

This runbook is for operators maintaining the Epic 19 zone layer: Grid Junction, 42 outer zones, daemon repop, and PvE XP. Run commands from the repo root unless noted.

## Rebuild From A Clean DB

For a local throwaway rebuild, stop Evennia, remove the local SQLite database if present, then run the normal setup path:

```bash
make migrate
cd gridwars && ../.venv/bin/python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings'); django.setup(); from world import build_grid; build_grid.build()"
```

`build_grid.build()` creates the core sectors, Grid Junction, zone topology, and all zone rooms through `world.zones.build_zones.build_all_zones()`. The builder is idempotent. On a clean DB, expect 42 zones built and a few hundred rooms. On a rerun, expect existing zones to be skipped rather than duplicated.

Do not use interactive `evennia migrate` in automation; it can prompt for superuser creation. Use `make migrate` or `python -m django migrate`.

## Re-Seed Zone Generation

Zone layout is deterministic from `world.zones.generator.generate_zone(archetype_id, variant_index)`. Re-seeding changes generated topology, room ordering, spawn-table placement, and prose selection for future builds. It does not rewrite already-created rooms because `build_all_zones()` skips zones found by tag.

To test a new seed policy, change the generator, run the zone generator tests, then rebuild from a clean DB. For production, treat re-seeding as a world rebuild/migration event: snapshot the database first, announce the content refresh, and verify Grid Junction exits after the build.

## Tune EXP Constants

PvE XP tuning lives in `gridwars/world/zones/exp.py`. The operator-facing constants are:

```python
KILL_BASE_MULT
BAND_MOD_STEP
SOFT_CAP_MULT
STRIKE_MULT
```

Change constants only with balance-harness output in hand. After edits, run `make test` or at minimum the EXP and balance tests under `gridwars/world/tests/`.

## Read Balance Harness Output

Use:

```bash
python bin/gridwars-balance.py
python bin/gridwars-balance.py --player-level 10 --archetype ice_wall
python bin/gridwars-balance.py --json
```

The table reports kill rate, average time-to-kill, XP per kill, XP per hour, daemon pressure, and review flags. `UNFARMABLE` usually means the sampled player level is not ready for that archetype. `TOO_LUCRATIVE` means XP/hour is high enough to inspect for farming exploits. JSON output is best for comparing before/after tuning runs.

## Add A New Archetype

This is a code change, not an ops-only task. Start with these surfaces:

- `gridwars/world/zones/archetypes.py` for the archetype prototype and level band.
- `gridwars/world/zones/prose_pools.py` for room names and descriptions.
- `gridwars/typeclasses/daemon_variants.py` for daemon class behavior.
- `gridwars/world/zones/build_zones.py` for distribution counts.
- `gridwars/world/build_grid.py` for Junction/deeper topology and gates.
- `gridwars/world/tests/` for generator, instantiation, topology, XP, and integration coverage.

Keep the total distribution intentional, rebuild from clean, then inspect both balance output and in-game traversal before shipping.
