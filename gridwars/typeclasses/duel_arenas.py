"""
GridWars.run instanced duel arena — Room typeclass with lifecycle.

A DuelArena is a transient Room created when two players accept a
challenge. It exists until the duel ends (LD3 declares a winner) or
the lifecycle timeout fires.

LD1 covers the data layer + lifecycle helpers. LD2 adds the
challenge/accept command protocol. LD3 adds the win mechanic.
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
