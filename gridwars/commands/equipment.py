"""
GridWars.run equipment commands — equip / unequip / inventory.

Equipped state stored on caller.db.equipped_disc (the Disc object).
Inventory reads caller.contents and filters to Disc instances.
ID3 combat-refactor will read caller.db.equipped_disc.damage_bonus
to compute strike damage.
"""
from evennia import Command


class CmdEquip(Command):
    """
    Equip an Identity Disc from your inventory.

    Usage:
      equip <disc>

    The disc must already be in your inventory. Replaces any
    previously-equipped disc (the prior disc stays in inventory).
    """

    key = "equip"
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        arg = self.args.strip()
        if not arg:
            caller.msg("|rUsage:|n |wequip <disc>|n")
            return
        target = caller.search(arg, location=caller, quiet=True)
        if isinstance(target, list):
            target = target[0] if target else None
        if target is None:
            caller.msg(f"|rNo '{arg}' in your inventory.|n")
            return
        if not target.is_typeclass("typeclasses.discs.Disc", exact=False):
            caller.msg(f"|r{target.key} is not an Identity Disc.|n")
            return
        caller.db.equipped_disc = target
        caller.msg(
            f"|gEquipped|n {target.key} — damage +{target.damage_bonus}, "
            f"cooldown {target.cooldown_seconds}s."
        )


class CmdUnequip(Command):
    """
    Unequip your currently-equipped Identity Disc.

    Usage:
      unequip

    The disc stays in your inventory. Strike falls back to base damage
    until you equip another disc.
    """

    key = "unequip"
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        current = caller.db.equipped_disc
        if not current:
            caller.msg("|yNothing equipped.|n")
            return
        caller.db.equipped_disc = None
        caller.msg(f"|gUnequipped|n {current.key}.")


class CmdInventory(Command):
    """
    List items you are carrying; mark the equipped disc.

    Usage:
      inventory
      inv
    """

    key = "inventory"
    aliases = ["inv"]
    locks = "cmd:all()"
    help_category = "GridWars"

    def func(self):
        caller = self.caller
        items = list(caller.contents)
        if not items:
            caller.msg("|yYou are carrying nothing.|n")
            return
        equipped = caller.db.equipped_disc
        lines = ["|wInventory:|n"]
        for item in items:
            tag = " |g[equipped]|n" if item is equipped else ""
            lines.append(f"  - {item.key}{tag}")
        caller.msg("\n".join(lines))
