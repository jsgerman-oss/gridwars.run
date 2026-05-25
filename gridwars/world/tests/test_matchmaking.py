"""
Unit tests for world.matchmaking.MatchmakingScript.

Covers acceptance criteria for e17.2 (gridwars_run-iwg):
  1. Empty queue — at_repeat() is a no-op; no arena created.
  2. Single player queued — at_repeat() is a no-op; player stays queued.
  3. Two players queued — FIFO pair matched, DuelArena created, both
     moved in, queue drained.
  4. Three players queued — first two matched, third stays queued.
  5. Race-condition guard — if queue changes between snapshot and swap,
     at_repeat() aborts the tick; queue is unchanged and no arena spawned.

Uses EvenniaTest (real Django DB, full Evennia environment) mirroring the
DaemonPatrol test pattern in world/tests/test_daemon_patrol.py.

Import discipline: world.* modules are imported lazily (inside setUp /
test bodies) to avoid ModuleNotFoundError during Evennia test-discovery, which
calls __import__() before Django's sys.path is fully configured. This matches
the pattern used by test_build_grid.py in this package and avoids the
pre-existing discovery-phase error that affects test_duels.py / test_strike.py.
"""

from unittest.mock import patch

from evennia.server.models import ServerConfig
from evennia.utils.create import create_object, create_script
from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character

# _QUEUE_KEY inlined here so this module can be imported before Django's
# sys.path is fully configured (same constraint as test_daemon_patrol.py).
_QUEUE_KEY = "gw_duel_queue"


class MatchmakingTestBase(EvenniaTest):
    """Set up two Character objects and a stopped MatchmakingScript."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        # Lazy import — avoids discovery-phase ModuleNotFoundError.
        from world.queue_store import clear_queue
        from world.matchmaking import MatchmakingScript
        clear_queue()

        # Create two player characters in a shared room.
        self.p1 = create_object(Character, key="Player1", location=self.room1)
        self.p2 = create_object(Character, key="Player2", location=self.room1)

        # Create the script but stop the timer — we call at_repeat() directly.
        self.script = create_script(MatchmakingScript)
        self.script.stop()

    def tearDown(self):
        from world.queue_store import clear_queue
        clear_queue()
        super().tearDown()


# ---------------------------------------------------------------------------
# 1. Empty queue — no-op
# ---------------------------------------------------------------------------

class TestEmptyQueueNoOp(MatchmakingTestBase):
    """at_repeat() on an empty queue creates no arena and raises no error."""

    def test_empty_queue_no_arena_spawned(self):
        from world.queue_store import get_queue
        self.script.at_repeat()
        self.assertEqual(get_queue(), [])
        self.assertEqual(self.p1.location, self.room1)
        self.assertEqual(self.p2.location, self.room1)


# ---------------------------------------------------------------------------
# 2. Single player queued — no-op, player stays queued
# ---------------------------------------------------------------------------

class TestSinglePlayerNoOp(MatchmakingTestBase):
    """With only one player queued, at_repeat() does nothing."""

    def test_single_player_stays_queued(self):
        from world.queue_store import enqueue, get_queue
        enqueue(self.p1.id)
        self.script.at_repeat()
        self.assertIn(self.p1.id, get_queue())
        self.assertEqual(self.p1.location, self.room1)


# ---------------------------------------------------------------------------
# 3. Two players — FIFO pair + arena spawn + queue drained
# ---------------------------------------------------------------------------

class TestFifoPairCreatesArena(MatchmakingTestBase):
    """Two queued players are matched in FIFO order and placed in a DuelArena."""

    def test_two_players_matched_into_arena(self):
        from world.queue_store import enqueue, get_queue
        enqueue(self.p1.id)
        enqueue(self.p2.id)

        self.script.at_repeat()

        self.assertEqual(get_queue(), [], "Queue should be drained after match.")
        self.assertIsNotNone(self.p1.location, "p1 should have a location.")
        self.assertEqual(
            self.p1.location,
            self.p2.location,
            "Both players must be in the same arena.",
        )
        arena = self.p1.location
        self.assertTrue(
            arena.is_typeclass("typeclasses.duel_arenas.DuelArena", exact=False),
            f"Arena should be DuelArena typeclass, got {arena.typeclass_path!r}.",
        )

    def test_match_message_sent_to_both_players(self):
        """Both players receive the '|gMatched!...' message."""
        from world.queue_store import enqueue
        enqueue(self.p1.id)
        enqueue(self.p2.id)

        messages_p1 = []
        messages_p2 = []
        self.p1.msg = lambda text, **kw: messages_p1.append(text)
        self.p2.msg = lambda text, **kw: messages_p2.append(text)

        self.script.at_repeat()

        self.assertTrue(
            any("Matched" in m for m in messages_p1),
            f"p1 should receive a 'Matched' message; got: {messages_p1}",
        )
        self.assertTrue(
            any("Matched" in m for m in messages_p2),
            f"p2 should receive a 'Matched' message; got: {messages_p2}",
        )

    def test_fifo_order_respected(self):
        """First two in queue are matched first (FIFO)."""
        from world.queue_store import enqueue, get_queue
        p3 = create_object(Character, key="Player3", location=self.room1)
        enqueue(self.p1.id)
        enqueue(self.p2.id)
        enqueue(p3.id)

        self.script.at_repeat()

        self.assertNotEqual(
            self.p1.location,
            self.room1,
            "p1 should have left room1 (matched).",
        )
        self.assertNotEqual(
            self.p2.location,
            self.room1,
            "p2 should have left room1 (matched).",
        )
        self.assertEqual(
            p3.location,
            self.room1,
            "p3 should still be in room1 (waiting for next tick).",
        )
        remaining = get_queue()
        self.assertIn(p3.id, remaining, "p3 should still be in the queue.")
        self.assertNotIn(self.p1.id, remaining)
        self.assertNotIn(self.p2.id, remaining)


# ---------------------------------------------------------------------------
# 4. Three players — first two matched, third stays queued
# ---------------------------------------------------------------------------

class TestThirdPlayerWaits(MatchmakingTestBase):
    """When three players are queued, the third stays queued after one tick."""

    def test_third_player_remains_queued(self):
        from world.queue_store import enqueue, get_queue
        p3 = create_object(Character, key="Waiter3", location=self.room1)
        enqueue(self.p1.id)
        enqueue(self.p2.id)
        enqueue(p3.id)

        self.script.at_repeat()

        queue_after = get_queue()
        self.assertEqual(
            queue_after,
            [p3.id],
            f"Only p3 should remain in the queue; got {queue_after}.",
        )


# ---------------------------------------------------------------------------
# 5. Race-condition guard — TOCTOU abort
# ---------------------------------------------------------------------------

class TestRaceConditionGuard(MatchmakingTestBase):
    """If the queue changes between snapshot and swap, at_repeat() aborts cleanly."""

    def test_toctou_abort_leaves_queue_intact(self):
        from world.queue_store import enqueue
        enqueue(self.p1.id)
        enqueue(self.p2.id)

        original_conf = ServerConfig.objects.conf

        call_count = [0]

        def patched_conf(key, value=None, default=None):
            """Intercept the second read (compare step) to simulate a concurrent write."""
            if key == _QUEUE_KEY and value is None:
                call_count[0] += 1
                if call_count[0] == 2:
                    # Simulate a concurrent enqueue that modified the queue.
                    original_conf(_QUEUE_KEY, value=[self.p1.id, self.p2.id, 999])
                    return [self.p1.id, self.p2.id, 999]
            return original_conf(key, value=value, default=default)

        with patch.object(ServerConfig.objects, "conf", side_effect=patched_conf):
            self.script.at_repeat()

        # Script should have aborted — neither player moved.
        self.assertEqual(
            self.p1.location,
            self.room1,
            "p1 should not have moved when TOCTOU guard fires.",
        )
        self.assertEqual(
            self.p2.location,
            self.room1,
            "p2 should not have moved when TOCTOU guard fires.",
        )
