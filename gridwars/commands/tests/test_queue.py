"""
Unit tests for CmdQueue (@queue duel|leave|status) and queue_store.

Covers 6 acceptance criteria for e17.1 (gridwars_run-1a0):
  1. @queue duel enqueues; @queue status shows position 1.
  2. Second character enqueues; status shows position 2 for them, 1 for first.
  3. @queue duel twice from same character is idempotent (no-op + message).
  4. @queue leave removes the character.
  5. @queue leave when not queued is a no-op + message.
  6. Persistence: write queue, reload queue_store module, state survives.

Uses EvenniaCommandTest (real Django DB, full Evennia environment).
char1 and char2 are placed in room1 by the base setUp.
"""

import importlib

from evennia.utils.test_resources import EvenniaCommandTest

from commands.queue import CmdQueue
from typeclasses.characters import Character
from world import queue_store


class QueueCommandTestCase(EvenniaCommandTest):
    """CmdQueue: all queue paths."""

    character_typeclass = Character

    def setUp(self):
        super().setUp()
        queue_store.clear_queue()

    def tearDown(self):
        queue_store.clear_queue()
        super().tearDown()

    def test_enqueue_shows_position_one(self):
        """@queue duel puts char1 in the queue; @queue status confirms position 1."""
        result = self.call(CmdQueue(), "duel", caller=self.char1)
        self.assertIn("joined", result)
        self.assertIn("1", result)
        status = self.call(CmdQueue(), "status", caller=self.char1)
        self.assertIn("1", status)

    def test_two_chars_positions(self):
        """char1 joins first (pos 1); char2 joins second (pos 2). Status reflects each."""
        self.call(CmdQueue(), "duel", caller=self.char1)
        result2 = self.call(CmdQueue(), "duel", caller=self.char2)
        self.assertIn("2", result2)
        status1 = self.call(CmdQueue(), "status", caller=self.char1)
        self.assertIn("1", status1)
        status2 = self.call(CmdQueue(), "status", caller=self.char2)
        self.assertIn("2", status2)

    def test_enqueue_idempotent(self):
        """@queue duel a second time from the same character is a no-op."""
        self.call(CmdQueue(), "duel", caller=self.char1)
        result = self.call(CmdQueue(), "duel", caller=self.char1)
        self.assertIn("already", result.lower())
        self.assertEqual(queue_store.get_queue().count(self.char1.id), 1)

    def test_leave_removes_char(self):
        """@queue leave removes char1 from the queue."""
        self.call(CmdQueue(), "duel", caller=self.char1)
        self.assertIn(self.char1.id, queue_store.get_queue())
        result = self.call(CmdQueue(), "leave", caller=self.char1)
        self.assertIn("left", result.lower())
        self.assertNotIn(self.char1.id, queue_store.get_queue())

    def test_leave_when_not_queued(self):
        """@queue leave when char is not in the queue returns a message without error."""
        result = self.call(CmdQueue(), "leave", caller=self.char1)
        self.assertIn("not in", result.lower())
        self.assertEqual(queue_store.get_queue(), [])

    def test_queue_persists_across_module_reload(self):
        """Queue state survives a module reload (ServerConfig is source of truth)."""
        queue_store.enqueue(self.char1.id)
        self.assertIn(self.char1.id, queue_store.get_queue())
        importlib.reload(queue_store)
        self.assertIn(self.char1.id, queue_store.get_queue())
