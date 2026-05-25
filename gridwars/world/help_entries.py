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
    # ---------------------------------------------------------------------------
    # Per-command full entries — Epic 18.2 prose fill
    # ---------------------------------------------------------------------------
    {
        "key": "status",
        "category": "GridWars",
        "text": """
|cstatus|n — Identity Disc HUD

|wUsage:|n
  |gstatus|n

Renders your Identity Disc readout: a neon-bordered panel showing your
character name, current sector, faction alignment, and all vital stats.

|wStats displayed:|n
  |wIntegrity|n — your hit points (0–100). If this hits 0 from a |gstrike|n,
    you are derezzed and respawn in Users' Sector with at least 25 restored.
  |wEnergy|n — action resource (0–100). Reserved for future mechanics.
  |wExp|n — accumulated experience points, earned by defeating opponents
    with |gstrike|n.
  |wRank|n — your current Grid rank label (e.g. "User"), updated as you
    gain experience.

Color coding gives you an immediate read on your condition:
  |gGreen|n  — 60% or above (healthy)
  |yYellow|n — 25–59% (take care)
  |rRed|n    — below 25% (critical; consider retreating)

If you are aligned with a faction, |gstatus|n also shows how many sectors
your faction currently controls across the Grid.

|wExample:|n
  > |gstatus|n
  |c╔══════════ IDENTITY DISC ══════════╗|n
    Name     Tron
    Sector   Combat Grid Alpha
    Faction  |cUsers|n
    Integrity |g 87|n / 100
    Energy    |g 50|n / 100
    Exp       |g120|n
    Rank      |cUser|n
  |c╚════════════════════════════════════╝|n
    Sectors  |g3|n held by your faction

|wSee also:|n |gscan|n, |gstrike|n, |gequip|n, |gleaderboard|n.
""",
    },
    {
        "key": "scan",
        "category": "GridWars",
        "text": """
|cscan|n — Tactical Sector View

|wUsage:|n
  |gscan|n

Produces a concise tactical read of your current sector. Where |glook|n
gives you the room's prose description, |gscan|n gives you intelligence:
who is present, how to leave, and who controls the sector.

|wOutput sections:|n
  |wSector name|n — the sector's canonical label at the top of the output.
  |wFlavor line|n — a one-line ambient read drawn from the sector's
    scan_flavor attribute, or the first sentence of its description when
    no dedicated flavor is set.
  |wPrograms here|n — all other Characters in the sector. Each entry is
    color-coded by faction: |cUsers cyan|n, |gPrograms green|n, |rDaemons red|n.
    Unaffiliated characters appear in yellow.
  |wExits|n — available cardinal exits (north, south, east, west) displayed
    in cyan. These are the same exits you traverse with movement commands.
  |wSector control|n — which faction holds this sector (or "unclaimed" if
    none has run |gcapture|n here yet).

|gscan|n excludes yourself from the "Programs here" list so you are not
listed alongside your targets. NPC Daemons appear in the list when they
are present and patrol-active.

|wExample:|n
  > |gscan|n
  |c-- |wSECTOR SCAN: Combat Grid Alpha|c --|n
  |yCircuit-lattice walls glow with residual energy.|n

  |wPrograms here:|n
    - |cFlynn|n |w[|nUsers|w]|n
    - |rDaemon-0001|n |w[|rDaemons|w]|n

  |wExits:|n |cnorth|n, |csouth|n, |cwest|n
  |wSector control:|n |cUsers|n

|wSee also:|n |gstatus|n, |glook|n, |gstrike|n, |gcapture|n.
""",
    },
    {
        "key": "strike",
        "category": "GridWars",
        "text": """
|cstrike|n — PvP Attack

|wUsage:|n
  |gstrike <target>|n

Launches an immediate attack against another character in your current
sector. No consent required. The target must be physically present — you
cannot strike across sectors.

|wDamage calculation:|n
  Each strike deals: |wbase (10)|n + |wrandom jitter (0–5)|n + |wdisc bonus|n
  The disc bonus comes from the damage_bonus property of your currently
  equipped Identity Disc. Without an equipped disc, the bonus is 0. A
  fully-leveled (L5) disc adds +13, making each strike land for 23–28.

|wCooldown:|n
  When a disc is equipped, its cooldown_seconds property applies between
  strikes. If you attempt to strike before the cooldown clears, you see
  the remaining seconds. Unequipped strike has no cooldown.

|wDefeat flow:|n
  When a target's integrity drops to 0, they are derezzed: the room sees
  a derezz broadcast, the target is moved to Users' Sector, and their
  integrity is restored to at least 25. You gain experience on victory.
  Characters are never permanently deleted.

|wRestrictions:|n
  You cannot strike yourself. You cannot strike non-Character objects.
  Strikes only resolve against Characters in the same sector.

|wExample:|n
  > |gstrike Flynn|n
  You strike |cFlynn|n with identity disc for |y18|n integrity.

  (If Flynn's integrity hits 0:)
  |gVictory.|n Experience +10. (Now: 130)

|wSee also:|n |gstatus|n, |gscan|n, |gchallenge|n, |gequip|n.
""",
    },
    {
        "key": "challenge",
        "category": "GridWars",
        "text": """
|cchallenge|n — Issue a Formal Duel Challenge

|wUsage:|n
  |gchallenge <target>|n

Sends a formal duel challenge to another character in your current sector.
Unlike |gstrike|n, a duel requires the target's consent before combat begins.
Once accepted, both players are transported to a private DuelArena where
only they can fight.

|wChallenge flow:|n
  1. You run |gchallenge <target>|n. The target receives a notification.
  2. Target has 30 seconds to type |gaccept|n or |gdecline|n.
  3. On |gaccept|n: both players enter the arena and the duel begins.
  4. On |gdecline|n or timeout: the challenge is cancelled; both parties
     are notified.

|wWin condition:|n
  First player to land 3 successful strikes wins. On the third strike:
  - Winner receives a victory message and gains experience.
  - Loser receives a defeat message.
  - Both are returned to the sector they were in before the duel.
  - ELO ratings update for both characters.
  - The arena is destroyed.

|wRestrictions:|n
  Target must be in your current sector. You cannot challenge yourself.
  You cannot challenge a character who already has a pending challenge.

|wExample:|n
  > |gchallenge Flynn|n
  Challenge sent to Flynn.
  (Flynn sees: "Tron has challenged you to a duel. Type |waccept|n or
   |wdecline|n within 30s.")

|wSee also:|n |gaccept|n, |gdecline|n, |gstrike|n, |g@queue|n.
""",
    },
    {
        "key": "accept",
        "category": "GridWars",
        "text": """
|caccept|n — Accept a Duel Challenge

|wUsage:|n
  |gaccept|n

Accepts the pending duel challenge directed at your character. You must
have received a challenge (via |gchallenge|n from another player) for this
command to do anything. There are no arguments — it acts on whichever
challenge is currently pending.

|wWhat happens on accept:|n
  Both you and the challenger are immediately transported to a newly-created
  private DuelArena room. No other players can enter this arena. The duel
  begins at once — there is no additional confirmation step.

  Inside the arena, use |gstrike <opponent>|n to fight. Standard combat rules
  apply: base damage plus jitter plus disc bonus, with cooldown enforced if
  a disc is equipped.

|wEdge case — integrity during the duel:|n
  If your integrity reaches 0 mid-duel, the normal respawn flow fires first
  (you are moved to Users' Sector with restored integrity). The strike-count
  check still resolves, so the duel can end cleanly even if you have been
  moved out of the arena before the final tally.

|wTimeout:|n
  If you do not respond within 30 seconds, the challenge expires. You will
  receive a notification and no duel is created. You do not need to type
  |gdecline|n — silence is treated as expiry.

|wExample:|n
  (After receiving a challenge from Tron:)
  > |gaccept|n
  Challenge accepted. Entering the arena...

|wSee also:|n |gchallenge|n, |gdecline|n, |gstrike|n.
""",
    },
    {
        "key": "decline",
        "category": "GridWars",
        "text": """
|cdecline|n — Decline a Duel Challenge

|wUsage:|n
  |gdecline|n

Declines the pending duel challenge directed at your character. Clears
the challenge state and notifies the challenger that you refused. No duel
is created, and neither player moves. Declining is immediate — it does
not require the 30-second window to expire.

|gdecline|n only acts on an active pending challenge. If you have no
challenge pending, you will see a "No pending challenge" message and
nothing else happens. The command is safe to run speculatively.

|wTimeout vs. explicit decline:|n
  You do not need to decline an expired challenge. Once the 30-second
  timer passes, the challenge clears automatically and both parties are
  notified of the expiry. Declining before the timeout simply resolves it
  immediately rather than making the challenger wait the full duration.

There is no penalty for declining a challenge. Your ELO rating does not
change. The challenger is free to issue another challenge afterward.

|wExample:|n
  (After receiving a challenge from Tron:)
  > |gdecline|n
  Declined.
  (Tron sees: "Flynn declined your challenge.")

|wSee also:|n |gchallenge|n, |gaccept|n.
""",
    },
    {
        "key": "equip",
        "category": "GridWars",
        "text": """
|cequip|n — Equip an Identity Disc

|wUsage:|n
  |gequip <disc>|n

Slots an Identity Disc from your inventory into your active equipment
slot. The disc must already be in your inventory (use |ginventory|n to
check). You can only have one disc equipped at a time.

|wEffect of equipping:|n
  An equipped disc modifies your combat output in two ways:
    |wDamage bonus|n — added to every |gstrike|n on top of base (10) + jitter (0–5).
    |wCooldown|n — minimum seconds between strikes. Without an equipped disc,
    strikes have no cooldown.

  The disc's level determines these values. A standard starter disc is
  level 1 (+5 damage bonus). A fully-leveled disc reaches level 5 (+13).

|wReplacing an equipped disc:|n
  Equipping a new disc when you already have one equipped replaces it
  automatically. The previously-equipped disc remains in your inventory;
  it is not lost or destroyed.

|wInventory requirement:|n
  The disc must be on your character (in your inventory), not on the
  floor or held elsewhere. If you cannot find your disc, try |ginventory|n
  to confirm it is present.

|wExample:|n
  > |gequip identity disc|n
  |gEquipped|n identity disc — damage +5, cooldown 3s.

|wSee also:|n |gunequip|n, |ginventory|n, |gstatus|n, |gstrike|n.
""",
    },
    {
        "key": "unequip",
        "category": "GridWars",
        "text": """
|cunequip|n — Unequip Your Identity Disc

|wUsage:|n
  |gunequip|n

Removes your currently-equipped Identity Disc from the active equipment
slot and returns it to inventory. No arguments are required — there is
only one equipment slot, so the command always acts on whatever is
currently slotted.

|wEffect of unequipping:|n
  Once unequipped, |gstrike|n reverts to base behavior: 10 + random jitter
  (0–5) damage with no cooldown. You lose the disc's damage bonus until
  you |gequip|n another disc.

  The disc is not deleted. It remains in your inventory and can be
  re-equipped at any time with |gequip <disc name>|n.

|wWhen to unequip:|n
  Typically you would only unequip to swap to a better disc. There is no
  tactical advantage to fighting bare-handed in the current implementation.

|wExample:|n
  > |gunequip|n
  |gUnequipped|n identity disc.

  (If nothing is equipped:)
  > |gunequip|n
  |yNothing equipped.|n

|wSee also:|n |gequip|n, |ginventory|n, |gstatus|n.
""",
    },
    {
        "key": "inventory",
        "aliases": ["inv"],
        "category": "GridWars",
        "text": """
|cinventory|n — List Carried Items

|wUsage:|n
  |ginventory|n
  |ginv|n

Lists every item your character is currently carrying. Each item is shown
on its own line. If you have a disc equipped, it is marked with a
|g[equipped]|n tag so you can identify your active loadout at a glance.

|wTypical output:|n
  Items you may carry include Identity Discs. New characters begin with
  a starter Identity Disc already in inventory (it is created at character
  creation). Additional discs can be obtained from administrators or, in
  future updates, from in-world vendors and drop mechanics.

|wRelationship to equip:|n
  |ginventory|n tells you what you have. |gequip <disc>|n slots one of those
  items. |gunequip|n moves the slotted item back to inventory. All three
  commands work together to manage your loadout.

|wExample:|n
  > |ginv|n
  |wInventory:|n
    - identity disc |g[equipped]|n
    - battle disc

  > |ginv|n   (when carrying nothing)
  |yYou are carrying nothing.|n

|wSee also:|n |gequip|n, |gunequip|n, |gstatus|n.
""",
    },
    {
        "key": "faction",
        "category": "GridWars",
        "text": """
|cfaction|n — Faction Alignment

|wUsage:|n
  |gfaction|n                 — list all factions and your current alignment
  |gfaction choose <name>|n   — align yourself with a faction (one-shot)

The Grid has three factions: |cUsers|n, |gPrograms|n, and |rDaemons|n. Every
character starts unaffiliated and must align via |gfaction choose|n before
they can meaningfully participate in sector-control gameplay.

|wFactions at a glance:|n
  |cUsers|n    — "Uploaded. Underestimated." The default arrival faction.
    Numerous, adaptive, and underestimated by the power structures.
  |gPrograms|n — "Order is the throughput." The Grid's native architecture.
    Structured, territorial, and deeply suspicious of unregistered processes.
  |rDaemons|n  — "We are the noise in your stack." Corrupted or unregistered
    processes that operate in the gaps the architecture ignores.

|wFaction effects:|n
  Your faction tag appears in |gscan|n output, color-coded for other players
  to see. Faction membership gates |gcapture|n. Your faction's held-sector
  count appears in your |gstatus|n readout. There are currently no mechanical
  bonuses tied to specific faction choice.

|wAlignment is permanent:|n
  |gfaction choose|n is a one-shot command. Once aligned, the Grid treats your
  faction as a code-level registration. Changing factions requires admin
  override. If you made an error on your first session, contact an admin.

|wExample:|n
  > |gfaction choose Users|n
  |gAlignment set:|n |cUsers|n. Uploaded. Underestimated.
  (Room sees: "Flynn has uploaded into the |cUsers|n.")

  > |gfaction|n
  (Lists all three factions with taglines, descriptions, and your current
  alignment at the bottom.)

|wSee also:|n |gstatus|n, |gcapture|n, |gscan|n, |ggridwars|n.
""",
    },
    {
        "key": "capture",
        "category": "GridWars",
        "text": """
|ccapture|n — Claim a Sector for Your Faction

|wUsage:|n
  |gcapture|n

Claims your current sector for your faction. Sector control is a
persistent layer tracked on the room itself — it survives server reloads
and persists until another faction captures the sector.

|wRequirements:|n
  You must be aligned with a faction (use |gfaction choose <name>|n first).
  You cannot capture while adrift between sectors (an edge case that
  should not occur during normal play).

|wCapture semantics:|n
  |wFriendly re-capture|n — if your faction already owns this sector, the
    command is a no-op. You see a confirmation but nothing changes.
  |wCross-faction capture|n — if a rival faction holds this sector, capture
    overwrites it immediately. There is currently no resistance mechanic;
    you do not need to defeat defenders first.

Sector control is visible in |gscan|n output ("Sector control: |cUsers|n")
and the number of sectors your faction holds appears in |gstatus|n. There
is no limit on how many sectors a faction can hold.

|wExample:|n
  > |gcapture|n
  |gCombat Grid Alpha|n is now under |cUsers|n control.
  (Room sees: "Flynn of |cUsers|n has claimed this sector for the Grid.")

  (If your faction already owns it:)
  > |gcapture|n
  |yCombat Grid Alpha|n is already held by |cUsers|n.

|wSee also:|n |gfaction|n, |gscan|n, |gstatus|n.
""",
    },
    {
        "key": "@queue",
        "aliases": ["queue"],
        "category": "GridWars",
        "text": """
|c@queue|n — Duel Matchmaking Queue

|wUsage:|n
  |g@queue|n              — show current queue status
  |g@queue status|n       — show current queue status
  |g@queue duel|n         — join the matchmaking queue
  |g@queue leave|n        — leave the matchmaking queue

The matchmaking queue is a server-side FIFO list of players waiting
for a duel. When two or more players are queued simultaneously, the
matchmaking script pairs the first two automatically (typically within
5 seconds) and routes them into a private DuelArena.

|wJoining the queue:|n
  |g@queue duel|n adds you to the end of the queue and tells you your
  position. You remain in the queue across movement — you can walk
  around while waiting. If you disconnect, your queue entry persists
  until you explicitly leave or are matched.

|wLeaving the queue:|n
  |g@queue leave|n removes you immediately. You receive a confirmation.
  If you were already matched before the command arrived, the match
  proceeds regardless.

|wDifference from challenge:|n
  |gchallenge <target>|n requires a specific opponent to consent.
  |g@queue duel|n matches you with whoever joins next — no specific
  target, no consent step. Use the queue when you want any opponent;
  use |gchallenge|n when you want a specific one.

|wDuel rules once matched:|n
  Same as direct challenges: first to 3 strikes wins, ELO ratings update
  afterward, both players return to their pre-duel sectors on conclusion.

|wExample:|n
  > |g@queue duel|n
  |gYou joined the duel queue.|n You are number |w1|n in line.

  (Second player joins; within ~5 seconds:)
  |gMatched! Entering arena...|n

  > |g@queue status|n   (while waiting)
  |wDuel queue:|n 1 waiting -- you are number |w1|n in line.

  > |g@queue leave|n
  |gYou left the duel queue.|n

|wSee also:|n |gchallenge|n, |gaccept|n, |gstrike|n, |gleaderboard|n.
""",
    },
    {
        "key": "leaderboard",
        "aliases": ["@leaderboard"],
        "category": "GridWars",
        "text": """
|cleaderboard|n — Top-10 ELO Rankings

|wUsage:|n
  |g@leaderboard|n
  |gleaderboard|n

Displays the top-10 ranked characters on the Grid, ordered by ELO rating
from highest to lowest. Ties are broken alphabetically by character name.
Each row shows rank, name, rating, and faction tag.

|wHow ratings work:|n
  Every character starts with a rating of 1000. After each duel (matched
  via |g@queue|n or direct |gchallenge|n), both participants' ratings update
  using the standard ELO formula with a K-factor of 32:

    Expected score for winner:
      E = 1 / (1 + 10^((loser_rating - winner_rating) / 400))
    Rating delta:
      delta = 32 * (1 - E)
      winner gains delta (rounded); loser loses delta (floored at 0)

  An upset win — lower-rated player defeating a higher-rated one —
  produces a larger swing than a win against a weaker opponent. The
  system self-corrects quickly as match volume accumulates.

|wPersistence:|n
  Ratings persist across sessions, logouts, and respawns. They reset only
  if explicitly wiped by an administrator. Your leaderboard standing is
  a permanent record of your performance.

|wOpen-sector strikes:|n
  Ratings update only after duels (challenge + accept, or @queue match).
  Casual |gstrike|n combat in open sectors does not affect ELO ratings.

|wExample:|n
  > |g@leaderboard|n
  |c╔══════════ GRID LEADERBOARD ═══════════╗|n
    |c#    Name                 Rating  Faction|n
     1    |wTron                |n  |g  1243|n |y[Users]|n
     2    |wFlynn               |n  |g  1198|n |y[Programs]|n
     3    |wSark                |n  |g  1150|n |y[Daemons]|n
  |c╚════════════════════════════════════════╝|n

|wSee also:|n |gstatus|n, |g@queue|n, |gchallenge|n.
""",
    },
    {
        "key": "north",
        "aliases": ["n"],
        "category": "General",
        "text": """
|cnorth|n — Move North

|wUsage:|n
  |gnorth|n
  |gn|n

Moves your character through the north exit of your current sector. The
exit must exist — if no north exit is present, you will see a "you cannot
go that way" message. Use |gscan|n or |glook|n to see which exits are
available in the current sector.

The Grid's sectors are connected in a loose cardinal lattice. Not every
sector has all four exits, and the geometry does not always form a
perfect grid — some sectors are dead ends, hubs with three exits, or
connected only diagonally by name.

Movement is instantaneous. Upon arrival the new sector renders its
description. Your location updates immediately for other players in
both the sector you left and the one you entered.

|wExample:|n
  > |gnorth|n
  (You move through the north exit; new sector description renders.)
  > |gn|n
  (Alias; identical effect.)

|wAlias:|n |gn|n

|wSee also:|n |gsouth|n, |geast|n, |gwest|n, |glook|n, |gscan|n.
""",
    },
    {
        "key": "south",
        "aliases": ["s"],
        "category": "General",
        "text": """
|csouth|n — Move South

|wUsage:|n
  |gsouth|n
  |gs|n

Moves your character through the south exit of your current sector. The
exit must exist — if no south exit is present, you will see a "you cannot
go that way" message. Use |gscan|n to check which exits are available
before committing to a direction.

Movement is instantaneous. On arrival the new sector's description renders
automatically; you can also type |glook|n to re-read it if the output
scrolled. Other players in both sectors see you leave and arrive.

The Grid's sector geometry is not a perfect square lattice — some sectors
have only one or two exits, some are hubs with three or four. Moving south
from one sector does not always bring you back north from the next. Explore
methodically and use |gscan|n's exit list to build a mental map.

|wExample:|n
  > |gsouth|n
  (You move through the south exit; new sector description renders.)
  > |gs|n
  (Alias; identical effect.)

|wAlias:|n |gs|n

|wSee also:|n |gnorth|n, |geast|n, |gwest|n, |glook|n, |gscan|n.
""",
    },
    {
        "key": "east",
        "aliases": ["e"],
        "category": "General",
        "text": """
|ceast|n — Move East

|wUsage:|n
  |geast|n
  |ge|n

Moves your character through the east exit of your current sector. The
exit must exist — if no east exit is present, you will see a "you cannot
go that way" message. Use |gscan|n to check which exits are available
before committing to a direction.

Movement is instantaneous. On arrival the new sector's description renders
automatically; you can also type |glook|n to re-read it if the output
scrolled. Other players in both sectors see you leave and arrive.

The Grid's sector geometry is not a perfect square lattice — some sectors
have only one or two exits, some are hubs with three or four. Moving east
from one sector does not always bring you back west from the next. Explore
methodically and use |gscan|n's exit list to build a mental map.

|wExample:|n
  > |geast|n
  (You move through the east exit; new sector description renders.)
  > |ge|n
  (Alias; identical effect.)

|wAlias:|n |ge|n

|wSee also:|n |gnorth|n, |gsouth|n, |gwest|n, |glook|n, |gscan|n.
""",
    },
    {
        "key": "west",
        "aliases": ["w"],
        "category": "General",
        "text": """
|cwest|n — Move West

|wUsage:|n
  |gwest|n
  |gw|n

Moves your character through the west exit of your current sector. The
exit must exist — if no west exit is present, you will see a "you cannot
go that way" message. Use |gscan|n to check which exits are available
before committing to a direction.

Movement is instantaneous. On arrival the new sector's description renders
automatically; you can also type |glook|n to re-read it if the output
scrolled. Other players in both sectors see you leave and arrive.

The Grid's sector geometry is not a perfect square lattice — some sectors
have only one or two exits, some are hubs with three or four. Moving west
from one sector does not always bring you back east from the next. Explore
methodically and use |gscan|n's exit list to build a mental map.

|wExample:|n
  > |gwest|n
  (You move through the west exit; new sector description renders.)
  > |gw|n
  (Alias; identical effect.)

|wAlias:|n |gw|n

|wSee also:|n |gnorth|n, |gsouth|n, |geast|n, |glook|n, |gscan|n.
""",
    },
    {
        "key": "look",
        "aliases": ["l"],
        "category": "General",
        "text": """
|clook|n — Render Current Sector

|wUsage:|n
  |glook|n
  |gl|n

Re-renders the full description of your current sector. On first arrival
in a sector the description renders automatically; use |glook|n any time
you want to refresh it — after the screen scrolls, after a burst of combat
messages, or simply to re-read the atmosphere.

|glook|n vs |gscan|n:
  |glook|n gives you the sector's prose description: the curated text written
  by the Grid architects, with ambient flavor and lore. It does not show
  which characters are present or who controls the sector. Use it for
  orientation, immersion, and reading the environment's narrative detail.

  |gscan|n gives you the tactical layer: characters present (faction-coded),
  available exits, and sector control. No prose. Use it for situational
  awareness before and during combat. The two commands complement each
  other — |glook|n for context, |gscan|n for intelligence.

|wExample:|n
  > |glook|n
  (Full sector prose description renders to your screen.)
  > |gl|n
  (Alias; identical effect.)

|wAlias:|n |gl|n

|wSee also:|n |gscan|n, |gnorth|n, |gsouth|n, |geast|n, |gwest|n.
""",
    },
    {
        "key": "say",
        "category": "General",
        "text": """
|csay|n — Speak in the Current Sector

|wUsage:|n
  |gsay <text>|n

Broadcasts a line of speech to everyone in your current sector. Your name
appears as the speaker. The message is visible only to characters in the
same sector as you — it does not broadcast globally or across sectors.

Speech is the primary channel for player-to-player communication in a
sector. It is local and spatial: walk to the same sector as the person
you want to talk to, then say what you need.

|wThere is no privacy in speech.|n Any character present — including
NPC Daemons during a patrol — sees every |gsay|n message. If you need
to communicate without others seeing, use a direct tell (stock Evennia
|gpage|n command) instead.

|wExample:|n
  > |gsay Hello, Grid.|n
  You say: "Hello, Grid."
  (Others in sector see: "|cFlynn|n says: 'Hello, Grid.'")

|wSee also:|n |gpose|n, |gwho|n.
""",
    },
    {
        "key": "pose",
        "category": "General",
        "text": """
|cpose|n — Emote an Action

|wUsage:|n
  |gpose <action>|n

Broadcasts a third-person emote to everyone in your current sector. Your
character name is prepended to the action text automatically. Use |gpose|n
for atmospheric roleplay, reactions, combat flavor, or any physical
expression that is not spoken dialogue.

Like |gsay|n, |gpose|n is local: only characters in your current sector see it.
It does not reach other sectors. Every character present — including NPC
Daemons on patrol — sees the emote output.

|wFormatting tip:|n
  The server prepends your name directly before your text. Write your action
  in the third person starting from a verb or possessive:

  > |gpose runs a diagnostic on the terminal.|n
  Flynn runs a diagnostic on the terminal.

  > |gpose 's disc glows faintly, humming at the edge of audibility.|n
  Flynn's disc glows faintly, humming at the edge of audibility.

  Notice the apostrophe-s pattern — start your text with |g's|n (including
  the space before it) to form a possessive naturally.

|wSee also:|n |gsay|n, |gwho|n.
""",
    },
    {
        "key": "who",
        "category": "General",
        "text": """
|cwho|n — List Connected Players

|wUsage:|n
  |gwho|n

Displays all characters currently connected and active in the game.
The list includes character names and may include session metadata
depending on Evennia's default who output. This is a global view —
it shows everyone online regardless of which sector they are in.

|gwho|n is useful for knowing the current population before deciding
whether to queue for a duel (|g@queue duel|n), seek out a specific player
by name, check whether any administrators are online, or simply get a
sense of the Grid's activity level.

|gwho|n shows connected players only, not all registered characters.
A character that has logged out does not appear even if their object
persists in the world. The list refreshes each time you run the command;
it does not auto-update.

If you want to communicate with a specific player, use |gsay|n in the same
sector or the stock Evennia |gpage|n command for private messages. |gwho|n
tells you who is online; finding them means navigating to their sector.

|wExample:|n
  > |gwho|n
  (List of currently connected character names renders to your screen.)

|wSee also:|n |gsay|n, |gpose|n, |gquit|n, |g@queue|n.
""",
    },
    {
        "key": "quit",
        "category": "General",
        "text": """
|cquit|n — Disconnect from GridWars

|wUsage:|n
  |gquit|n

Ends your current session and disconnects from the server. Your character
object remains in the world (Evennia's default behavior) until the session
fully detaches. Other players may briefly see your character in |gscan|n
after you quit; it clears within the normal server tick.

|wPersistence on logout:|n
  All stats, faction alignment, inventory, disc XP, equipped disc, and
  ELO rating are saved permanently to the database. Nothing is lost when
  you quit. Reconnect with |gconnect <name> <password>|n and continue
  exactly where you left off.

|wIf you are in a duel:|n
  Disconnecting mid-duel leaves your character in the arena until the
  session times out. Your opponent's strikes against your idle character
  still count. If they reach 3 strikes, the duel resolves in their favor
  and your rating updates as a loss. Reconnecting quickly may allow you
  to resume fighting.

|wExample:|n
  > |gquit|n
  (Session ends; you are disconnected from the server.)

|wSee also:|n |gwho|n.
""",
    },
    {
        "key": "help",
        "category": "General",
        "text": """
|chelp|n — Display Command Help

|wUsage:|n
  |ghelp|n                 — show the help index (all categories)
  |ghelp <topic>|n         — display help for a specific command or topic

The help system covers every player-facing command in GridWars plus
general Evennia commands (movement, social, account management). To see
everything available, type |ghelp|n with no arguments and browse the index
by category.

|wGridWars categories:|n
  |wGridWars|n — game-specific commands: status, scan, strike, faction,
    challenge, equip, inventory, @queue, leaderboard, capture.
  |wGeneral|n — movement, look, say, pose, who, quit, help, and other
    stock Evennia commands.

|wFinding a command:|n
  If you know part of a command name, try |ghelp <partial>|n — Evennia
  searches for partial matches. For example, |ghelp inv|n may resolve to
  the inventory entry.

|wFor a broad game overview:|n
  |ghelp gridwars|n (or |ghelp gw|n) shows the full GridWars welcome index
  with a command summary organized by function. Start there if you are new.

|wExample:|n
  > |ghelp strike|n
  (Displays the strike entry with usage, damage math, and examples.)

  > |ghelp gw|n
  (Displays the GridWars master overview.)

|wSee also:|n |ggridwars|n, |gstatus|n, |gscan|n.
""",
    },
]
