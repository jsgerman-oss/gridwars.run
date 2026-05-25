"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom

from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    def at_object_leave(self, moved_obj, destination, **kwargs):
        """Clear combat_active when the last player-account leaves.

        Called by Evennia after any object departs this room. We check
        whether any Account-puppeted characters remain; if none do, combat
        cannot still be in progress and we clear the flag so the repop
        ticker is free to act. Covers normal movement and disconnect events.
        """
        super().at_object_leave(moved_obj, destination, **kwargs)
        self._maybe_clear_combat_active()

    def _maybe_clear_combat_active(self):
        """Clear combat_active when no player-account characters remain."""
        if not self.db.combat_active:
            return  # Fast path: flag already off.

        for obj in self.contents:
            if hasattr(obj, "account") and obj.account:
                return  # At least one live player remains — keep flag set.

        # No puppeted players remain; safe to clear.
        from world.room_state import clear_combat_active

        clear_combat_active(self)
