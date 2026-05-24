"""
GridWars.run Character typeclass.

Subclasses evennia.DefaultCharacter (via ObjectParent mixin), adds persistent
stats and atomic mutator helpers. Combat math lives in Epic 6; faction
validation in Epic 5. This file's only job is stat storage + clamping.
"""

from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import AttributeProperty

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    GridWars character with persistent stats.

    Attributes (all DB-backed via AttributeProperty):
        integrity (int): Hit points. Range [0, 100].
        energy    (int): Action resource. Range [0, 100].
        experience(int): Accumulated XP. Range [0, ∞).
        faction   (str|None): Player faction tag. Epic 5 validates; stored
                              here as a free-form string.
        grid_rank (str): Rank label within faction. Free-form for now.
    """

    integrity = AttributeProperty(default=100)
    energy = AttributeProperty(default=50)
    experience = AttributeProperty(default=0)
    faction = AttributeProperty(default=None)
    grid_rank = AttributeProperty(default="User")

    def at_object_creation(self):
        """
        Called once when this object is first created.

        AttributeProperty handles defaults automatically, but we set them
        explicitly here as belt-and-suspenders so the values are always
        present on fresh objects even if a future subclass skips super().
        """
        super().at_object_creation()
        if self.integrity is None:
            self.integrity = 100
        if self.energy is None:
            self.energy = 50
        if self.experience is None:
            self.experience = 0
        if self.grid_rank is None:
            self.grid_rank = "User"
        # faction intentionally left as None when unset; Epic 5 assigns it.

    # ------------------------------------------------------------------
    # Stat mutators — each clamps to its respective range.
    # No combat math here; these are pure stat-mutation primitives.
    # ------------------------------------------------------------------

    def take_damage(self, amount: int) -> int:
        """
        Subtract *amount* from integrity, floor at 0.

        Negative amounts are treated as 0 (no accidental healing).

        Args:
            amount (int): Damage to apply. Negative values are ignored.

        Returns:
            int: New integrity value after clamping.
        """
        new = max(0, self.integrity - max(0, amount))
        self.integrity = new
        return new

    def heal(self, amount: int, cap: int | None = None) -> int:
        """
        Add *amount* to integrity, ceil at *cap* (default 100).

        Negative amounts are treated as 0 (no accidental damage).

        Args:
            amount (int): HP to restore. Negative values are ignored.
            cap (int | None): Upper bound on resulting integrity.
                              Defaults to 100 when None.

        Returns:
            int: New integrity value after clamping.
        """
        ceiling = cap if cap is not None else 100
        new = min(ceiling, self.integrity + max(0, amount))
        self.integrity = new
        return new

    def gain_experience(self, amount: int) -> int:
        """
        Add *amount* to experience, floor at 0.

        Allows negative amounts so callers can deduct XP on penalties;
        result is clamped so experience never goes below zero.

        Args:
            amount (int): XP delta (may be negative).

        Returns:
            int: New experience value after clamping.
        """
        new = max(0, self.experience + amount)
        self.experience = new
        return new

    def reset_for_respawn(self, min_integrity: int = 25) -> None:
        """
        Restore integrity to at least *min_integrity* without touching
        energy, experience, faction, or grid_rank.

        Used by Epic 6 on defeat. If current integrity is already above
        *min_integrity*, it is left unchanged (no free bonus HP on respawn).

        Args:
            min_integrity (int): Floor to apply to integrity. Defaults to 25.
        """
        self.integrity = max(min_integrity, self.integrity)
