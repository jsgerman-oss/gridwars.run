"""
GridWars.run instanced duel arena — Room typeclass with lifecycle.

A DuelArena is a transient Room created when two players accept a
challenge. It exists until the duel ends (LD3 declares a winner) or
the lifecycle timeout fires.

LD1 covers the data layer + lifecycle helpers. LD2 adds the
challenge/accept command protocol. LD3 adds the win mechanic.

combat_active: set when the first participant enters via at_object_receive;
cleared by world.duels.end_arena before the arena is deleted.
"""
from evennia.objects.objects import DefaultRoom
from evennia.typeclasses.attributes import AttributeProperty

from .objects import ObjectParent


class DuelArena(ObjectParent, DefaultRoom):
    """A short-lived Room hosting a 1v1 duel."""

    participants = AttributeProperty(default=list)       # list of Character IDs
    origins = AttributeProperty(default=dict)            # char_id -> origin room ID
    started_at = AttributeProperty(default=None)         # ISO timestamp
    max_duration_seconds = AttributeProperty(default=60)
    winner_id = AttributeProperty(default=None)

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """Set combat_active when an Account-puppeted participant enters."""
        super().at_object_receive(moved_obj, source_location, **kwargs)
        if hasattr(moved_obj, "account") and moved_obj.account:
            from world.room_state import set_combat_active

            set_combat_active(self)
