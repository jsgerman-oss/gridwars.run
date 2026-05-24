"""
Unit tests for world.build_grid.build().

Covers (gridwars_run-62h.2 / Epic 9):
  1. build() creates exactly 5 rooms and 8 exits tagged with ('gridwars-core', 'world_build').
  2. build() is idempotent — calling it twice produces the same counts.
  3. The Users' Sector room is findable by its slug tag.

Uses EvenniaTest (real Django DB, full Evennia environment).

Import strategy: build_grid.py calls build() unconditionally at module scope
(line 177: `build()`). The module-level call fires at import time, before the
test DB is ready, and raises OperationalError.

We sidestep this by building a synthetic module stub that exposes only `build`
and delegates to the real function body — loaded lazily inside setUp() after
the test DB is live. The stub module is injected into sys.modules so the real
module file is never executed at collection time.

This avoids any circular-patch problem (patch() itself imports the target
module, which would trigger build()).
"""

import sys
import types

from evennia.utils.search import search_tag
from evennia.utils.test_resources import EvenniaTest


def _load_build_fn():
    """
    Execute build_grid.py's module body inside a temporary namespace that
    suppresses the top-level build() call, then return the real build function.

    We compile and exec the source manually so we can intercept the bare
    `build()` call at the bottom before it hits a cold DB.
    """
    import ast
    import pathlib

    src_path = pathlib.Path(__file__).parent.parent / "build_grid.py"
    source = src_path.read_text()

    # Parse and strip the last bare `build()` expression statement.
    tree = ast.parse(source, filename=str(src_path))
    stmts = tree.body
    # The last statement is `Expr(value=Call(func=Name(id='build')))`.
    if (
        stmts
        and isinstance(stmts[-1], ast.Expr)
        and isinstance(stmts[-1].value, ast.Call)
        and isinstance(stmts[-1].value.func, ast.Name)
        and stmts[-1].value.func.id == "build"
    ):
        tree.body = stmts[:-1]

    code = compile(tree, filename=str(src_path), mode="exec")

    module_ns = {"__name__": "world.build_grid", "__file__": str(src_path)}
    # We need evennia's create/search available.  exec with a namespace that
    # has them pre-imported; build_grid uses `from X import Y` at its top
    # so we let exec handle those naturally.
    exec(code, module_ns)  # noqa: S102
    return module_ns["build"], module_ns


class BuildGridTestCase(EvenniaTest):
    """world.build_grid.build() — room/exit counts, idempotency, slug lookup."""

    CATEGORY = "world_build"
    TAG_KEY = "gridwars-core"

    def setUp(self):
        super().setUp()
        # Load the real build function now that the test DB is live.
        self._build_fn, self._bg_ns = _load_build_fn()
        # Run the initial build.
        self._build_fn()

    def _tagged_objects(self):
        """Return all objects tagged (TAG_KEY, CATEGORY)."""
        return search_tag(key=self.TAG_KEY, category=self.CATEGORY)

    def _rooms(self, tagged):
        """Filter to room objects (no non-None destination)."""
        return [
            o for o in tagged
            if not (hasattr(o, "destination") and o.destination is not None)
        ]

    def _exits(self, tagged):
        """Filter to exit objects (have a non-None destination)."""
        return [
            o for o in tagged
            if hasattr(o, "destination") and o.destination is not None
        ]

    # ------------------------------------------------------------------
    # 1. 5 rooms + 8 exits created
    # ------------------------------------------------------------------

    def test_build_creates_5_rooms_and_8_exits(self):
        """After build(), count 5 rooms and 8 exits tagged gridwars-core/world_build."""
        tagged = self._tagged_objects()
        rooms = self._rooms(tagged)
        exits = self._exits(tagged)
        self.assertEqual(
            len(rooms), 5,
            f"Expected 5 rooms, got {len(rooms)}: {[r.key for r in rooms]}\n"
            f"All tagged ({len(tagged)}): "
            f"{[(o.key, getattr(o, 'destination', '(no dest)')) for o in tagged]}",
        )
        self.assertEqual(
            len(exits), 8,
            f"Expected 8 exits, got {len(exits)}: {[e.key for e in exits]}",
        )

    # ------------------------------------------------------------------
    # 2. build() is idempotent
    # ------------------------------------------------------------------

    def test_build_is_idempotent(self):
        """Calling build() twice leaves room and exit counts unchanged."""
        self._build_fn()

        tagged = self._tagged_objects()
        rooms = self._rooms(tagged)
        exits = self._exits(tagged)
        self.assertEqual(
            len(rooms), 5,
            f"Idempotency fail — rooms: expected 5, got {len(rooms)}",
        )
        self.assertEqual(
            len(exits), 8,
            f"Idempotency fail — exits: expected 8, got {len(exits)}",
        )

    # ------------------------------------------------------------------
    # 3. Users' Sector resolves via slug tag
    # ------------------------------------------------------------------

    def test_build_users_sector_resolves(self):
        """search_tag('users_sector', category='world_build') returns exactly 1 room."""
        results = search_tag(key="users_sector", category=self.CATEGORY)
        self.assertEqual(
            len(results), 1,
            f"Expected 1 users_sector room, got {len(results)}: {[r.key for r in results]}",
        )
        self.assertEqual(results[0].key, "Users' Sector")
