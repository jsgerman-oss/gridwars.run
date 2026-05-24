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

# Point new-character spawn at Users' Sector (built by world.build_grid).
# START_LOCATION must be a dbref string — Evennia passes it directly to
# ObjectDB.objects.get_id(), which does not accept a callable.
# After running `evennia batchcode world.build_grid` for the first time,
# confirm the Users' Sector dbref with:
#   evennia shell -c "from evennia.utils.search import search_tag; r=search_tag('users_sector', category='world_build'); print(r[0].dbref if r else 'not found')"
# then update this value if it differs from the default #2.
START_LOCATION = "#2"

# Use the GridWars Character subclass for every new character.
# Path is relative to the gridwars/ game dir per Evennia convention.
BASE_CHARACTER_TYPECLASS = "typeclasses.characters.Character"

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
