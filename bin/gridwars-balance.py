#!/usr/bin/env python3
"""
GridWars balance-tuning CLI (e19.10).

Run this script from the repo root to simulate combat across all zone
archetypes and report XP/hour, kill rate, and risk profile for each
(player_level, archetype) pair.  No DB or Evennia runtime required.

Usage::

    python bin/gridwars-balance.py
    python bin/gridwars-balance.py --player-level 5 --player-level 20
    python bin/gridwars-balance.py --archetype datastream --player-level 5
    python bin/gridwars-balance.py --json
    python bin/gridwars-balance.py --player-level 10 --n-runs 2000
    python bin/gridwars-balance.py --single --player-level 5 --archetype ice_wall --daemon-level 9

Output modes:
  default  ASCII table with flagged anomalies
  --json   JSON array of all rows, one object per (player, archetype) pair

Flags in the output:
  UNFARMABLE     XP/hour < 10 AND kill rate < 5%  (zone inaccessible to this level)
  TOO_LUCRATIVE  XP/hour > 50,000 (potential exploit, needs tuning)
"""

import argparse
import json
import sys
import os

# Make the gridwars package importable when running from repo root or bin/.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_GW_PKG = os.path.join(_REPO_ROOT, "gridwars")
for _p in [_REPO_ROOT, _GW_PKG]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from world.zones.balance_harness import (
    simulate_combat,
    sweep_all_zones,
    format_table,
    ARCHETYPES,
)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="GridWars balance-tuning harness — simulate PvE XP/hour across zones.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--player-level", "-p",
        dest="player_levels",
        type=int,
        action="append",
        metavar="LEVEL",
        help="Player level(s) to simulate. May be repeated. Default: 1 5 10 20 30 40",
    )
    parser.add_argument(
        "--archetype", "-a",
        dest="archetypes",
        action="append",
        choices=sorted(ARCHETYPES),
        metavar="ARCHETYPE",
        help=f"Archetype(s) to include. Choices: {sorted(ARCHETYPES)}. Default: all.",
    )
    parser.add_argument(
        "--n-runs",
        dest="n_runs",
        type=int,
        default=1000,
        help="Monte Carlo runs per (player, archetype) pair (default 1000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for reproducible output (default 42).",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit JSON array instead of ASCII table.",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help=(
            "Run a single (player, archetype, daemon_level) simulation and print "
            "the full BalanceReport.  Requires --player-level, --archetype, and "
            "--daemon-level."
        ),
    )
    parser.add_argument(
        "--daemon-level",
        dest="daemon_level",
        type=int,
        help="Daemon level for --single mode.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    if args.single:
        # Validate required args for --single mode.
        missing = []
        if not args.player_levels:
            missing.append("--player-level")
        if not args.archetypes:
            missing.append("--archetype")
        if args.daemon_level is None:
            missing.append("--daemon-level")
        if missing:
            print(f"--single requires: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)

        report = simulate_combat(
            player_lvl=args.player_levels[0],
            daemon_archetype=args.archetypes[0],
            daemon_lvl=args.daemon_level,
            n_runs=args.n_runs,
            seed=args.seed,
        )
        if args.as_json:
            print(report.to_json())
        else:
            print(report)
        return

    # Sweep mode — all archetypes × all player levels.
    player_levels = args.player_levels or [1, 5, 10, 20, 30, 40]
    rows = sweep_all_zones(
        player_levels=player_levels,
        n_runs=args.n_runs,
        seed=args.seed,
    )

    # Filter by archetype if --archetype was passed.
    if args.archetypes:
        rows = [r for r in rows if r.archetype in args.archetypes]

    if not rows:
        print("No rows matched the given filters.", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps([r.to_dict() for r in rows], indent=2))
    else:
        print(format_table(rows))
        flagged = [r for r in rows if r.flag]
        if flagged:
            print(f"\n[!] {len(flagged)} flagged row(s) require review.")


if __name__ == "__main__":
    main()
