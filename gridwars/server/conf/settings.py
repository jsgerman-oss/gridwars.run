r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

######################################################################
# GridWars.run overrides
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "GridWars.run"

######################################################################
# World + Character wiring (Epic 3 W2 + Epic 4 C2)
######################################################################

# Use the GridWars Account subclass.  Its create_character() override
# resolves spawn location via tag lookup ("users_sector", "world_build")
# at runtime, making START_LOCATION below a true last-resort fallback only.
BASE_ACCOUNT_TYPECLASS = "typeclasses.accounts.Account"

# Use the GridWars Character subclass for every new character.
# Path is relative to the gridwars/ game dir per Evennia convention.
BASE_CHARACTER_TYPECLASS = "typeclasses.characters.Character"

# Fallback spawn location used only when tag lookup finds no Users' Sector
# (e.g. first boot before `evennia batchcode world.build_grid` has run).
# Evennia's DefaultAccount.create_character() passes this to
# ObjectDB.objects.get_id(), which requires a dbref string — not a callable.
# Limbo (#2) is the safe default; characters will move to Users' Sector on
# the next grid build + reconnect.
START_LOCATION = "#2"

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
