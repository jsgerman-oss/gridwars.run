"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

import random

from evennia.scripts.scripts import DefaultScript


PATROL_INTERVAL = 30  # seconds between ticks


class Script(DefaultScript):
    """
    This is the base TypeClass for all Scripts. Scripts describe
    all entities/systems without a physical existence in the game world
    that require database storage (like an economic system or
    combat tracker). They
    can also have a timer/ticker component.

    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties (check docs for full listing, this could be
      outdated).

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     create(key, **kwargs)
     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_pause()
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_script_delete()
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.
      at_server_start()

    """

    pass


class DaemonPatrol(DefaultScript):
    """Move every Daemon to a random adjacent sector on each tick.

    Does NOT engage targets (DA3 adds sense+engage). Starts after a
    one-interval delay so server boot settles before the first move.
    """

    def at_script_creation(self):
        self.key = "daemon_patrol"
        self.desc = "Daemon NPC patrol Script"
        self.interval = PATROL_INTERVAL
        self.persistent = True
        self.start_delay = True

    def at_repeat(self):
        from typeclasses.daemons import Daemon

        for daemon in Daemon.objects.all():
            self._step_one(daemon)

    def _step_one(self, daemon):
        loc = daemon.location
        if not loc:
            return
        exits = [e for e in loc.contents if e.destination is not None]
        if not exits:
            return
        # Only move to gridwars-core tagged sectors, not Limbo or OOC areas.
        valid_exits = [
            e
            for e in exits
            if e.destination
            and e.destination.tags.has("gridwars-core", category="world_build")
        ]
        if not valid_exits:
            return
        chosen = random.choice(valid_exits)
        daemon.move_to(chosen.destination, quiet=True)

        # Sense: any non-Daemon Character in this room after moving?
        if not daemon.location:
            return
        targets = [
            obj for obj in daemon.location.contents
            if obj is not daemon
            and obj.is_typeclass("typeclasses.characters.Character", exact=False)
            and getattr(obj, "faction", None) != "Daemons"
        ]
        if not targets:
            return
        # Engage: strike the first sensed target via the existing CmdStrike code
        # path. execute_cmd triggers the full strike flow (damage, messages,
        # defeat respawn, attacker XP) without duplicating any combat logic.
        target = targets[0]
        daemon.execute_cmd(f"strike {target.key}")
