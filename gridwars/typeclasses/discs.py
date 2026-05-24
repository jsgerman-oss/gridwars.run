"""
GridWars.run Identity Disc — wieldable weapons.

Subclasses Evennia's DefaultObject. Stores damage_bonus, cooldown_seconds,
disc_class as AttributeProperty fields. The strike command (ID3 refactor)
reads damage_bonus when this disc is equipped.

Discs are inert until ID2 wires equip/unequip and ID3 refactors strike.
"""
from evennia.objects.objects import DefaultObject
from evennia.typeclasses.attributes import AttributeProperty


class Disc(DefaultObject):
    """Wieldable identity disc with damage bonus + cooldown."""

    damage_bonus = AttributeProperty(default=5)
    cooldown_seconds = AttributeProperty(default=3)
    disc_class = AttributeProperty(default="standard")

    def at_object_creation(self):
        super().at_object_creation()
        # Belt-and-suspenders — AttributeProperty defaults already cover this.
        if self.damage_bonus is None:
            self.damage_bonus = 5
        if self.cooldown_seconds is None:
            self.cooldown_seconds = 3
        if self.disc_class is None:
            self.disc_class = "standard"

    def get_display_desc(self, looker, **kwargs):
        return (
            f"A glowing identity disc. Class: {self.disc_class}. "
            f"Damage bonus: +{self.damage_bonus}. Cooldown: {self.cooldown_seconds}s."
        )
