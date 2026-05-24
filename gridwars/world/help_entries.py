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
                       Users' Sector with restored integrity. Attackers
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
scan the Combat Grid (|wnorth, east, north|n |cfrom Users' Sector).|n
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
]
