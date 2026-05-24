"""
GridWars.run Daemon NPC typeclass.

Subclasses Character. NPCs have no Account (they're not playable).
Faction is auto-set to "Daemons" on creation. DA2 adds the patrol
Script; DA3 adds the sense+engage logic.

Daemons share the Character respawn/defeat flow — when killed by a
player they reset_for_respawn and move back to Daemon Gate (via the
search_tag pattern established by W2-followup).
"""
from typeclasses.characters import Character


class Daemon(Character):
    """Autonomous corrupted process. NPC subclass of Character."""

    def at_object_creation(self):
        super().at_object_creation()
        # Daemons are always aligned with the Daemons faction.
        self.faction = "Daemons"

    def at_post_puppet(self, **kwargs):
        # No login/logout messaging for NPCs.
        pass

    def at_pre_unpuppet(self, **kwargs):
        # NPCs are never puppeted by an Account.
        pass

    def reset_for_respawn(self, min_integrity: int = 25) -> None:
        """Daemons respawn at Daemon Gate, not Users' Sector."""
        super().reset_for_respawn(min_integrity=min_integrity)
        from evennia.utils.search import search_tag
        gate = search_tag("daemon_gate", category="world_build")
        if gate:
            self.location = gate[0]
