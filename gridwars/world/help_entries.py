"""
File-based help entries. These complements command-based help and help entries
added in the database using the `sethelp` command in-game.

Control where Evennia reads these entries with `settings.FILE_HELP_ENTRY_MODULES`,
which is a list of python-paths to modules to read.

A module like this should hold a global `HELP_ENTRY_DICTS` list, containing
dicts that each represent a help entry. If no `HELP_ENTRY_DICTS` variable is
given, all top-level variables that are dicts in the module are read as help
entries.

Each dict is on the form
::

    {'key': <str>,
     'text': <str>}``     # the actual help text. Can contain # subtopic sections
     'category': <str>,   # optional, otherwise settings.DEFAULT_HELP_CATEGORY
     'aliases': <list>,   # optional
     'locks': <str>       # optional, 'view' controls seeing in help index, 'read'
                          #           if the entry can be read. If 'view' is unset,
                          #           'read' is used for the index. If unset, everyone
                          #           can read/view the entry.

"""

HELP_ENTRY_DICTS = [
    {
        "key": "gridwars",
        "aliases": ["gw"],
        "category": "GridWars",
        "text": """
|cWelcome to GridWars.run.|n

Full PvP. No limits. Free to play. Open source.

|wInfo commands|n
  |gstatus|n            Identity disc HUD (integrity, energy, exp, rank)
  |gscan|n              Tactical sector view (programs + exits + flavor)
  |ghelp <command>|n    Command-specific help (any command in this index)

|wFaction commands|n (|cUsers|n / |gPrograms|n / |rDaemons|n)
  |gfaction|n                List factions + your current alignment
  |gfaction choose <name>|n  Align (one-shot; admin override required to change)

|wCombat commands|n
  |gstrike <target>|n  Same-sector PvP strike; defeat sends target back to
                       Users\' Sector with restored integrity. Attackers
                       gain experience on victory. Characters are never
                       deleted.

|wMovement|n
  |gnorth|n / |gsouth|n / |geast|n / |gwest|n   Move via named exits (aliased n/s/e/w)
  |glook|n                          Re-render the current sector

|wSocial|n (stock Evennia)
  |gsay <text>|n      Speak in the current sector
  |gpose <action>|n   Emote
  |gwho|n             List connected players
  |gquit|n            Disconnect

|c→ Start by choosing a faction (|wfaction choose Users|n |cor any other), then
scan the Combat Grid (|wnorth, east, north|n |cfrom Users\' Sector).|n
        """,
    },
    {
        "key": "evennia",
        "aliases": ["ev"],
        "category": "General",
        "locks": "read:perm(Developer)",
        "text": """
            Evennia is a MU-game server and framework written in Python. You can read more
            on https://www.evennia.com.

            # subtopics

            ## Installation

            You'll find installation instructions on https://www.evennia.com.

            ## Community

            There are many ways to get help and communicate with other devs!

            ### Discussions

            The Discussions forum is found at https://github.com/evennia/evennia/discussions.

            ### Discord

            There is also a discord channel for chatting - connect using the
            following link: https://discord.gg/AJJpcRUhtF

        """,
    },
    # ---------------------------------------------------------------------------
    # Per-command stub entries - prose fill comes in e18.2
    # ---------------------------------------------------------------------------
    {
        "key": "status",
        "category": "GridWars",
        "text": """
|cstatus|n - Identity disc HUD: integrity, energy, experience, rank.

|wUsage:|n |gstatus|n

|wSee also:|n scan, strike, equip.
""",
    },
    {
        "key": "scan",
        "category": "GridWars",
        "text": """
|cscan|n - Tactical sector view: programs present, exits, and ambient flavor.

|wUsage:|n |gscan|n

|wSee also:|n status, look, strike.
""",
    },
    {
        "key": "strike",
        "category": "GridWars",
        "text": """
|cstrike|n - Launch a PvP attack against a target in your current sector.

|wUsage:|n |gstrike <target>|n

|wSee also:|n status, scan, challenge.
""",
    },
    {
        "key": "challenge",
        "category": "GridWars",
        "text": """
|cchallenge|n - Issue a formal duel challenge to another player.

|wUsage:|n |gchallenge <target>|n

|wSee also:|n accept, decline, strike.
""",
    },
    {
        "key": "accept",
        "category": "GridWars",
        "text": """
|caccept|n - Accept a pending duel challenge from another player.

|wUsage:|n |gaccept <challenger>|n

|wSee also:|n challenge, decline.
""",
    },
    {
        "key": "decline",
        "category": "GridWars",
        "text": """
|cdecline|n - Decline a pending duel challenge.

|wUsage:|n |gdecline <challenger>|n

|wSee also:|n challenge, accept.
""",
    },
    {
        "key": "equip",
        "category": "GridWars",
        "text": """
|cequip|n - Equip a disc or weapon from your inventory.

|wUsage:|n |gequip <item>|n

|wSee also:|n unequip, inventory, status.
""",
    },
    {
        "key": "unequip",
        "category": "GridWars",
        "text": """
|cunequip|n - Remove an equipped disc or weapon and return it to inventory.

|wUsage:|n |gunequip <item>|n

|wSee also:|n equip, inventory, status.
""",
    },
    {
        "key": "inventory",
        "category": "GridWars",
        "text": """
|cinventory|n - List all items you are carrying (equipped and unequipped).

|wUsage:|n |ginventory|n

|wSee also:|n equip, unequip, status.
""",
    },
    {
        "key": "faction",
        "category": "GridWars",
        "text": """
|cfaction|n - List factions and check or set your alignment.

|wUsage:|n |gfaction|n or |gfaction choose <name>|n

|wSee also:|n status, gridwars.
""",
    },
    {
        "key": "north",
        "category": "General",
        "aliases": ["n"],
        "text": "|cnorth|n - Move through the north exit of the current sector. Alias: |gn|n.",
    },
    {
        "key": "south",
        "category": "General",
        "aliases": ["s"],
        "text": "|csouth|n - Move through the south exit of the current sector. Alias: |gs|n.",
    },
    {
        "key": "east",
        "category": "General",
        "aliases": ["e"],
        "text": "|ceast|n - Move through the east exit of the current sector. Alias: |ge|n.",
    },
    {
        "key": "west",
        "category": "General",
        "aliases": ["w"],
        "text": "|cwest|n - Move through the west exit of the current sector. Alias: |gw|n.",
    },
    {
        "key": "look",
        "category": "General",
        "aliases": ["l"],
        "text": "|clook|n - Re-render the current sector description. Alias: |gl|n.",
    },
    {
        "key": "say",
        "category": "General",
        "text": "|csay|n - Speak aloud in the current sector. Usage: |gsay <text>|n",
    },
    {
        "key": "pose",
        "category": "General",
        "text": "|cpose|n - Emote an action in the current sector. Usage: |gpose <action>|n",
    },
    {
        "key": "who",
        "category": "General",
        "text": "|cwho|n - List all currently connected players.",
    },
    {
        "key": "quit",
        "category": "General",
        "text": "|cquit|n - Disconnect from GridWars.",
    },
    {
        "key": "help",
        "category": "General",
        "text": """
|chelp|n - Display help for a command or topic.

|wUsage:|n |ghelp|n or |ghelp <topic>|n

|wSee also:|n gridwars.
""",
    },
]
