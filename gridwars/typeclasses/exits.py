"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit
from evennia.typeclasses.attributes import AttributeProperty

from .objects import ObjectParent


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property and overrides some hooks
    and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects child classes like this.

    """

    pass


class LevelGateExit(DefaultExit):
    """
    An exit that refuses traversal when the traversing object's player level
    is below ``min_level``.

    Player level is derived from the equipped identity disc level (1-5).
    If no disc is equipped the player is treated as level 0 and will be
    refused unless ``min_level`` is also 0.

    DB attribute:
        min_level (int): Minimum disc level required to pass. Default 1.

    Usage (in build scripts)::

        exit_obj = create_object(
            typeclass="typeclasses.exits.LevelGateExit",
            key="east",
            location=grid_junction,
            destination=zone_entry_room,
        )
        exit_obj.db.min_level = 5

    Refuse message (TRON-flavored):
        "The barrier rezzes solid against your disc -- you are too small for
        what is past this point. [Required: level {min_level}.]"
    """

    min_level = AttributeProperty(default=1)

    def _player_level(self, traversing_object) -> int:
        """Return the player's current level from their equipped disc.

        Falls back to 0 if no disc is equipped so ungated (min_level=0) exits
        are still traversable and the gate logic is uniformly expressed as
        ``player_level < min_level``.
        """
        disc = traversing_object.db.equipped_disc
        if disc is None:
            return 0
        try:
            return int(disc.level)
        except (AttributeError, TypeError, ValueError):
            return 0

    def at_traverse(self, traversing_object, target_location, **kwargs):
        """Refuse traversal when the player's disc level is below min_level."""
        required = int(self.min_level) if self.min_level is not None else 1
        player_level = self._player_level(traversing_object)

        if player_level < required:
            traversing_object.msg(
                f"The barrier rezzes solid against your disc -- you are too small "
                f"for what is past this point. [Required: level {required}.]"
            )
            return False

        return super().at_traverse(traversing_object, target_location, **kwargs)
