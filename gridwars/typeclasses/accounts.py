"""
Account

The Account represents the game "account" and each login has only one
Account object. An Account is what chats on default channels but has no
other in-game-world existence. Rather the Account puppets Objects (such
as Characters) in order to actually participate in the game world.


Guest

Guest accounts are simple low-level accounts that are created/deleted
on the fly and allows users to test the game without the commitment
of a full registration. Guest accounts are deactivated by default; to
activate them, add the following line to your settings file:

    GUEST_ENABLED = True

You will also need to modify the connection screen to reflect the
possibility to connect with a guest account. The setting file accepts
several more options for customizing the Guest account system.

"""

from evennia.accounts.accounts import DefaultAccount, DefaultGuest
from evennia.utils.search import search_tag


class Account(DefaultAccount):
    """
    GridWars account subclass.

    Overrides create_character() to resolve the new-character spawn location
    via tag lookup ("users_sector", category="world_build") at runtime.  This
    avoids the fragile START_LOCATION="#2" dbref in settings.py, which was
    only correct when Users' Sector happened to be the second object created
    and broke silently after any world rebuild.

    Hook used: create_character() — DefaultAccount instance method,
    vendor/evennia/evennia/accounts/accounts.py lines 931-976.  Lines 961-962
    show that location is set from settings.START_LOCATION when not provided
    in kwargs; we inject it here before the super() call.
    """

    def create_character(self, *args, **kwargs):
        """
        Resolve spawn location via tag lookup before delegating to Evennia.

        If no explicit location is passed by the caller, search for an object
        tagged ("users_sector", "world_build").  If found, use it as both
        location and home.  If not found (world not yet built, or first boot),
        fall through to Evennia's default behaviour which reads START_LOCATION
        from settings — so a documented fallback "#2" or similar still works.
        """
        if "location" not in kwargs:
            results = search_tag("users_sector", category="world_build")
            if results:
                kwargs["location"] = results[0]
                kwargs.setdefault("home", results[0])
        return super().create_character(*args, **kwargs)


class Guest(DefaultGuest):
    """
    This class is used for guest logins. Unlike Accounts, Guests and their
    characters are deleted after disconnection.
    """

    pass
