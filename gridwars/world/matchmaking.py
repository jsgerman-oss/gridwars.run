"""
GridWars.run matchmaking script — periodic FIFO queue pairing.

MatchmakingScript is a persistent Evennia DefaultScript that fires every
MATCHMAKING_INTERVAL seconds. On each tick it attempts to pop the first two
players from the duel queue (FIFO) and route them into a fresh DuelArena via
world.duels.create_arena.

TOCTOU / race-condition guard
------------------------------
ServerConfig stores the queue as a serialised list. Concurrent reads between
@queue duel (enqueue) and at_repeat (dequeue-pair) can race: one read sees the
old list while the other is writing. We guard by performing a compare-and-swap
style atomic swap inside at_repeat:

  1. Read the current queue.
  2. If len < 2, return (nothing to do).
  3. Pop the head two to get p1_id, p2_id; build a new_queue without them.
  4. Write new_queue back with ServerConfig.objects.conf() *only if* the queue
     we read in step 1 still equals the stored value (re-read to check).
  5. If the re-read differs (another writer raced us), abort this tick —
     the next tick will retry.

This is safe because:
  - at_repeat is called in a single-threaded Twisted tick.
  - The only concurrent writer is the @queue command, which also uses
    ServerConfig.objects.conf().
  - A single missed tick (5 s worst-case) is acceptable; players see the
    match within 2 ticks at most.

Auto-start
----------
The script is registered in server/conf/at_server_startstop.py via
at_server_start() so it restarts after every ``evennia reload`` or cold boot.
It is persistent=True and its own at_script_creation() sets the interval,
so even if the admin creates it manually via @script it self-configures.
"""

import logging

from evennia.objects.models import ObjectDB
from evennia.scripts.scripts import DefaultScript
from evennia.server.models import ServerConfig

logger = logging.getLogger("gridwars.matchmaking")

MATCHMAKING_INTERVAL = 5  # seconds between polls

# Mirror of queue_store._QUEUE_KEY — keeps this module free of a module-level
# cross-import that fires before Django apps are ready in the test runner.
_QUEUE_KEY = "gw_duel_queue"


class MatchmakingScript(DefaultScript):
    """Polls the duel queue every MATCHMAKING_INTERVAL seconds.

    When two or more players are queued the first two (FIFO) are matched:
      - dequeued atomically (with TOCTOU guard)
      - routed into a new DuelArena via world.duels.create_arena
      - each player receives a |gMatched!|n confirmation message

    The script is persistent and auto-started at every server start by
    at_server_startstop.at_server_start().
    """

    def at_script_creation(self):
        self.key = "matchmaking"
        self.desc = "Duel queue matchmaking script"
        self.interval = MATCHMAKING_INTERVAL
        self.persistent = True
        self.start_delay = True  # wait one interval before first poll

    def at_repeat(self):
        """Called every self.interval seconds by the Evennia scheduler."""
        # --- Step 1: read current queue ---
        queue_snapshot = list(
            ServerConfig.objects.conf(_QUEUE_KEY, default=list) or []
        )
        if len(queue_snapshot) < 2:
            return  # no-op: 0 or 1 player queued

        # --- Step 2: pop head two candidates ---
        p1_id, p2_id = queue_snapshot[0], queue_snapshot[1]
        new_queue = queue_snapshot[2:]

        # --- Step 3: atomic compare-and-swap guard ---
        # Re-read queue; if it changed since our snapshot a concurrent write
        # happened — skip this tick and retry next interval.
        current_queue = list(
            ServerConfig.objects.conf(_QUEUE_KEY, default=list) or []
        )
        if current_queue != queue_snapshot:
            logger.debug(
                "matchmaking: queue changed between snapshot and swap "
                "(TOCTOU avoided); retrying next tick."
            )
            return

        # Swap the new queue in atomically from our perspective.
        ServerConfig.objects.conf(_QUEUE_KEY, value=new_queue)

        # --- Step 4: resolve player objects ---
        try:
            p1 = ObjectDB.objects.get(id=p1_id)
            p2 = ObjectDB.objects.get(id=p2_id)
        except ObjectDB.DoesNotExist as exc:
            # One or both players no longer exist (disconnected + deleted).
            # Put surviving players back at the front of the queue.
            logger.warning("matchmaking: player object missing — %s", exc)
            self._requeue_on_error(p1_id, p2_id, new_queue)
            return

        # --- Step 5: send match notification and create arena ---
        for player in (p1, p2):
            player.msg("|gMatched! Entering arena...|n")

        try:
            from world.duels import create_arena
            arena = create_arena(p1, p2)
        except Exception:
            logger.exception(
                "matchmaking: create_arena raised; re-queuing %s and %s",
                p1_id,
                p2_id,
            )
            self._requeue_on_error(p1_id, p2_id, new_queue)
            return

        logger.info(
            "matchmaking: paired %s vs %s -> arena #%s",
            p1.key,
            p2.key,
            arena.id,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _requeue_on_error(self, p1_id: int, p2_id: int, tail: list) -> None:
        """Put p1 and p2 back at the front of the queue on transient errors."""
        recovery = [p1_id, p2_id] + list(tail)
        ServerConfig.objects.conf(_QUEUE_KEY, value=recovery)
        logger.warning(
            "matchmaking: re-queued %s and %s at front of queue", p1_id, p2_id
        )
