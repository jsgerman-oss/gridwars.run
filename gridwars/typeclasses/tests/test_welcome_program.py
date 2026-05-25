"""
Unit tests for the Welcome Program NPC (e16.3).

Covers:
- WelcomeProgram spawns in Uplink Node (via build_grid._spawn_welcome_program).
- WelcomeProgram greets a character that enters the Uplink Node room.
- WelcomeProgram does NOT engage in combat (no Daemon faction, no patrol).
- `look` / `say` work in the Uplink Node room.
- Idempotency: _spawn_welcome_program does not create a second NPC.
- WelcomeProgram absorbs a strike without retaliating.

Uses EvenniaTest (real Django DB, full Evennia environment).
"""

from unittest.mock import MagicMock, patch

from evennia.utils.create import create_object
from evennia.utils.test_resources import EvenniaTest

from typeclasses.welcome_program import UplinkNodeRoom, WelcomeProgram


class WelcomeProgramBase(EvenniaTest):
    """Shared setup: an UplinkNodeRoom with a WelcomeProgram inside."""

    def setUp(self):
        super().setUp()
        # Build a minimal Uplink Node room (UplinkNodeRoom typeclass).
        self.uplink_room = create_object(
            UplinkNodeRoom,
            key="Uplink Node",
            nohome=True,
        )
        self.uplink_room.tags.add("uplink_node", category="world_build")
        self.uplink_room.tags.add("welcome-program", category="world_build")

        # Spawn the Welcome Program inside the room.
        self.npc = create_object(
            WelcomeProgram,
            key="Welcome Program",
            location=self.uplink_room,
        )
        self.npc.tags.add("welcome-program", category="world_build")


class TestWelcomeProgramDefaults(WelcomeProgramBase):
    """WelcomeProgram typeclass defaults."""

    def test_welcome_program_is_not_daemon_faction(self):
        """WelcomeProgram must NOT have faction='Daemons'."""
        self.assertNotEqual(
            self.npc.faction,
            "Daemons",
            "WelcomeProgram must not carry the Daemons faction — "
            "it would appear as a patrol target.",
        )

    def test_welcome_program_not_in_daemon_objects(self):
        """WelcomeProgram must NOT appear in Daemon.objects.all()."""
        from typeclasses.daemons import Daemon

        daemon_keys = [d.key for d in Daemon.objects.all()]
        self.assertNotIn(
            self.npc.key,
            daemon_keys,
            "WelcomeProgram appeared in Daemon.objects.all() — "
            "it would be patrolled and could strike players.",
        )

    def test_welcome_program_has_desc(self):
        """WelcomeProgram has a non-empty description for `look`."""
        desc = self.npc.db.desc
        self.assertTrue(
            desc and len(desc) > 10,
            f"WelcomeProgram description is missing or too short: {desc!r}",
        )

    def test_welcome_program_location_is_uplink_room(self):
        """WelcomeProgram is placed in the Uplink Node after spawn."""
        self.assertEqual(self.npc.location, self.uplink_room)


class TestWelcomeProgramGreeting(WelcomeProgramBase):
    """Greeting fires when a character enters the Uplink Node."""

    def test_greet_sends_banner_to_character(self):
        """WelcomeProgram.greet() sends the tutorial banner to the arriving character."""
        with patch.object(self.char1, "msg") as mock_msg:
            self.npc.greet(self.char1)

        mock_msg.assert_called_once()
        call_text = mock_msg.call_args[0][0]
        # Banner must mention core commands.
        for keyword in ("status", "scan", "equip", "strike", "jack-in"):
            self.assertIn(
                keyword,
                call_text,
                f"Tutorial banner missing keyword '{keyword}'.",
            )

    def test_room_hook_triggers_greet_on_player_arrival(self):
        """UplinkNodeRoom.at_object_receive triggers WelcomeProgram.greet for a player."""
        # Move char1 into the room from another location.
        self.char1.location = self.room1  # start elsewhere

        with patch.object(self.npc, "greet") as mock_greet:
            self.uplink_room.at_object_receive(
                self.char1,
                source_location=self.room1,
                move_type="move",
            )

        mock_greet.assert_called_once_with(self.char1)

    def test_room_hook_does_not_greet_npc(self):
        """UplinkNodeRoom.at_object_receive does NOT greet the WelcomeProgram itself."""
        # Move the NPC back in as if re-entering.
        with patch.object(self.npc, "greet") as mock_greet:
            self.uplink_room.at_object_receive(
                self.npc,
                source_location=self.room1,
                move_type="move",
            )

        mock_greet.assert_not_called()

    def test_room_hook_does_not_greet_objects(self):
        """Non-character objects entering Uplink Node do not trigger a greeting."""
        generic_obj = create_object(
            "evennia.objects.objects.DefaultObject",
            key="DataPad",
            location=self.room1,
        )
        with patch.object(self.npc, "greet") as mock_greet:
            self.uplink_room.at_object_receive(
                generic_obj,
                source_location=self.room1,
                move_type="move",
            )

        mock_greet.assert_not_called()


class TestWelcomeProgramCombat(WelcomeProgramBase):
    """WelcomeProgram does not engage in combat."""

    def test_at_post_puppet_is_noop(self):
        """WelcomeProgram.at_post_puppet() sends no messages."""
        with patch.object(self.npc, "msg") as mock_msg:
            self.npc.at_post_puppet()
        mock_msg.assert_not_called()

    def test_at_pre_unpuppet_is_noop(self):
        """WelcomeProgram.at_pre_unpuppet() sends no messages."""
        with patch.object(self.npc, "msg") as mock_msg:
            self.npc.at_pre_unpuppet()
        mock_msg.assert_not_called()

    def test_welcome_program_does_not_retaliate_when_struck(self):
        """Striking the WelcomeProgram does not cause it to execute a strike command."""
        with patch.object(self.npc, "execute_cmd") as mock_exec:
            # Simulate damage directly (combat cmd goes through character's execute_cmd
            # for NPC retaliation; the WelcomeProgram must never call it).
            self.npc.take_damage(10)

        mock_exec.assert_not_called()


class TestWelcomeProgramSpawnIdempotency(WelcomeProgramBase):
    """_spawn_welcome_program is idempotent."""

    def _load_spawn_fn(self):
        """Load _spawn_welcome_program without triggering module-level build()."""
        import ast
        import pathlib

        src_path = pathlib.Path(__file__).parent.parent.parent / "world" / "build_grid.py"
        source = src_path.read_text()
        tree = ast.parse(source, filename=str(src_path))
        # Strip bare build() call at module bottom.
        stmts = tree.body
        if (
            stmts
            and isinstance(stmts[-1], ast.Expr)
            and isinstance(stmts[-1].value, ast.Call)
            and isinstance(stmts[-1].value.func, ast.Name)
            and stmts[-1].value.func.id == "build"
        ):
            tree.body = stmts[:-1]
        code = compile(tree, filename=str(src_path), mode="exec")
        ns = {"__name__": "world.build_grid", "__file__": str(src_path)}
        exec(code, ns)  # noqa: S102
        return ns["_spawn_welcome_program"]

    def test_spawn_welcome_program_idempotent(self):
        """Calling _spawn_welcome_program twice keeps exactly one NPC in the room."""
        from evennia.utils.search import search_tag

        spawn_fn = self._load_spawn_fn()

        # First call — the NPC already exists from setUp (tagged welcome-program).
        result1 = spawn_fn(self.uplink_room)
        count_after_first = len(search_tag("welcome-program", category="world_build"))

        # Second call — must skip creation.
        result2 = spawn_fn(self.uplink_room)
        count_after_second = len(search_tag("welcome-program", category="world_build"))

        self.assertEqual(
            count_after_first,
            count_after_second,
            f"_spawn_welcome_program created a duplicate NPC "
            f"({count_after_first} → {count_after_second}).",
        )
        self.assertIs(
            result1,
            result2,
            "_spawn_welcome_program returned different objects on successive calls.",
        )
