"""
GridWars.run — Welcome Program NPC typeclass (e16.3).

A non-hostile tutorial daemon that lives in the Uplink Node.  It greets
new players when they enter the room, explains core commands, and never
retaliates when struck.

Design notes
------------
* Subclasses ``Character`` directly — NOT ``Daemon``.  The DaemonPatrol
  script iterates ``Daemon.objects.all()``, which would drag the Welcome
  Program into the combat patrol loop.  By inheriting from Character we
  stay invisible to that query.
* ``at_object_creation`` sets ``faction`` to ``None`` (not "Daemons") so
  the program does not show up as a hostile faction target.
* ``at_object_receive`` is overridden on the Uplink Node room (see
  ``build_grid._spawn_welcome_program``), but the WelcomeProgram also
  exposes a ``greet()`` method that the room hook calls — this keeps the
  greeting logic in one place, testable independently of the room.
* Combat hooks ``sense`` / ``engage`` do not exist on Character; no
  override needed.  ``execute_cmd("strike ...")`` from the patrol script
  is never called because we are not a Daemon.  A player who issues
  ``strike welcome program`` will go through the normal strike command;
  the WelcomeProgram simply absorbs the hit with no retaliation (it has
  no combat AI).
"""

from evennia.objects.objects import DefaultRoom

from typeclasses.characters import Character

# ---------------------------------------------------------------------------
# Tutorial banner text
# ---------------------------------------------------------------------------

WELCOME_BANNER = r"""|c
  _____ _____ ____  ____   __        ___    ____  ____
 / ____|  __  |  _ \|  _ \ \ \      / / \  |  _ \/ ___|
| |  __| |__| | | | | | | | \ \ /\ / / _ \ | |_) \___ \
| | |_ |  _ /| |_| | |_| |  \ V  V / ___ \|  _ < ___) |
 \_____|_|  \_|____/|____/    \_/\_/_/   \_|_| \_|____/

|n
|wYou have been initialized.|n  I am the |gWelcome Program|n, a resident
process of the Uplink Node.  My function is to orient new arrivals.

|wCORE COMMANDS|n
  |gstatus|n         — Identity disc HUD: integrity, energy, XP, rank
  |gscan|n           — Tactical sector view (exits, programs, threat level)
  |glook|n           — Re-render your current sector

|wMOVEMENT|n
  |gnorth|n / |gsouth|n / |geast|n / |gwest|n   (or n / s / e / w)
  |gjack-in|n / |gji|n                     — Leave the Uplink Node

|wCOMBAT|n
  |gequip <disc>|n   — Ready your identity disc for combat
  |gstrike <target>|n — Initiate a same-sector attack

|wSOCIAL|n
  |gsay <text>|n     — Speak in the current sector
  |gpose <action>|n  — Emote

|wHELP|n
  |ghelp gridwars|n  — Full command reference
  |ghelp <command>|n — Command-specific detail

|c→ When you are ready, type |wjack-in|c (or |wji|c) to enter the Grid.|n
"""


class WelcomeProgram(Character):
    """
    Non-hostile tutorial NPC.  Lives in the Uplink Node.

    Greets every character that enters the room.  Does not patrol,
    does not strike, does not retaliate.
    """

    def at_object_creation(self):
        super().at_object_creation()
        # Explicitly not a Daemon — no faction tag.
        self.faction = None
        # Cosmetic description shown by `look` and `scan`.
        self.db.desc = (
            "|gWelcome Program|n — a luminous figure whose edges are too clean "
            "to be real, standing at the centre of the node. "
            "A soft cyan pulse runs from its feet to the crown of its head "
            "in a repeating diagnostic loop. "
            "It carries no disc. It has never needed one."
        )

    # ------------------------------------------------------------------
    # Greeting
    # ------------------------------------------------------------------

    def greet(self, arriving_character) -> None:
        """
        Send the tutorial banner to *arriving_character*.

        Args:
            arriving_character: Any Object/Character that just entered
                the Uplink Node room.
        """
        arriving_character.msg(WELCOME_BANNER)
        # Narrate the greeting to the room so other players see it.
        if self.location:
            self.location.msg_contents(
                f"|gWelcome Program|n turns toward {arriving_character.key} "
                f"and begins its orientation sequence.",
                exclude=[arriving_character],
            )

    # ------------------------------------------------------------------
    # Room arrival hook — trigger greet when a character enters our room
    # ------------------------------------------------------------------

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """
        Called on *this NPC* when something arrives in the same room —
        but DefaultObject.at_object_receive fires on the *container* (room),
        not on residents.

        The actual hook is ``UplinkNodeRoom.at_object_receive`` wired in
        build_grid; this method is here for completeness and direct-call
        testing only.
        """
        pass  # greeting is triggered by the room hook, not the NPC directly

    # ------------------------------------------------------------------
    # Login / logout — NPCs have no Account
    # ------------------------------------------------------------------

    def at_post_puppet(self, **kwargs):
        pass

    def at_pre_unpuppet(self, **kwargs):
        pass


# ---------------------------------------------------------------------------
# Uplink Node room typeclass
# ---------------------------------------------------------------------------


class UplinkNodeRoom(DefaultRoom):
    """
    Custom room typeclass for the Uplink Node (e16.3).

    Overrides ``at_object_receive`` to trigger the Welcome Program greeting
    whenever a Character (player) enters.  Only Characters receive the
    greeting — exits, objects, and other NPCs are silently ignored.

    The Welcome Program is located by the ``welcome-program / world_build``
    tag so the room does not hold a direct object reference (which would
    break across server reloads).
    """

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        """Greet arriving players via the Welcome Program."""
        super().at_object_receive(moved_obj, source_location, move_type=move_type, **kwargs)

        # Only greet Characters (players), not exits or other objects.
        if not moved_obj.is_typeclass("typeclasses.characters.Character", exact=False):
            return
        # Skip NPCs — the WelcomeProgram itself subclasses Character.
        if moved_obj.is_typeclass("typeclasses.welcome_program.WelcomeProgram", exact=False):
            return

        from evennia.utils.search import search_tag

        npcs = search_tag("welcome-program", category="world_build")
        for npc in npcs:
            if npc.location == self and hasattr(npc, "greet"):
                npc.greet(moved_obj)
                break
