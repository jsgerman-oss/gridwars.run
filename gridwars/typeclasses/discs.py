"""
GridWars.run Identity Disc — wieldable weapons.

Subclasses Evennia's DefaultObject. Stores damage_bonus, cooldown_seconds,
disc_class as AttributeProperty fields. The strike command (ID3 refactor)
reads damage_bonus when this disc is equipped.

Discs gain XP on strikes/kills and level up through 5 tiers, increasing
damage_bonus with each level.
"""
from evennia.objects.objects import DefaultObject
from evennia.typeclasses.attributes import AttributeProperty

# XP required to reach each level (index = level - 1).
XP_THRESHOLDS = [0, 100, 300, 700, 1500]

XP_PER_STRIKE = 10
XP_PER_KILL = 50


def damage_for(level: int) -> int:
    """Return damage_bonus for the given level (L1=5, L2=7, ..., L5=13)."""
    return 5 + (level - 1) * 2


class Disc(DefaultObject):
    """Wieldable identity disc with damage bonus + cooldown + XP leveling."""

    damage_bonus = AttributeProperty(default=5)
    cooldown_seconds = AttributeProperty(default=3)
    disc_class = AttributeProperty(default="standard")
    level = AttributeProperty(default=1)
    xp = AttributeProperty(default=0)

    def at_object_creation(self):
        super().at_object_creation()
        # Belt-and-suspenders — AttributeProperty defaults already cover this.
        if self.damage_bonus is None:
            self.damage_bonus = 5
        if self.cooldown_seconds is None:
            self.cooldown_seconds = 3
        if self.disc_class is None:
            self.disc_class = "standard"
        if self.level is None:
            self.level = 1
        if self.xp is None:
            self.xp = 0

    def gain_xp(self, amount: int) -> None:
        """Accumulate XP and level up if a threshold is crossed."""
        self.xp += amount
        self._level_up()

    def _level_up(self) -> None:
        """Check thresholds and advance level while XP qualifies, capped at L5."""
        max_level = len(XP_THRESHOLDS)
        while self.level < max_level:
            next_threshold = XP_THRESHOLDS[self.level]  # index = level (0-based next level)
            if self.xp < next_threshold:
                break
            self.level += 1
            self.damage_bonus = damage_for(self.level)
            # Notify the holder if the disc is currently equipped (location is a Character).
            loc = self.location
            if loc and loc.is_typeclass(
                "typeclasses.characters.Character", exact=False
            ):
                loc.msg(
                    f"|gDisc leveled up to L{self.level}! Damage bonus now {self.damage_bonus}.|n"
                )

    def get_display_desc(self, looker, **kwargs):
        return (
            f"A glowing identity disc. Class: {self.disc_class}. "
            f"Damage bonus: +{self.damage_bonus}. Cooldown: {self.cooldown_seconds}s. "
            f"Level: {self.level}."
        )
