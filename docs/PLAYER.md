# GridWars.run — Player Guide

**Full PvP. No deletion. No pay-to-win. Free to play.**

This guide covers everything you need to survive the Grid: how to connect, what every command does, how duels work, faction lore, and answers to the most common questions.

---

## Table of Contents

1. [Connect](#connect)
2. [First Five Minutes](#first-five-minutes)
3. [Command Reference](#command-reference)
4. [Lightcycle Duel Mechanics](#lightcycle-duel-mechanics)
5. [Faction Lore](#faction-lore)
6. [Rating and Leaderboard](#rating-and-leaderboard)
7. [Disc XP and Leveling](#disc-xp-and-leveling)
8. [FAQ](#faq)

---

## Connect

### Telnet

```
telnet game.gridwars.run 4000
```

Any terminal with telnet works. On macOS the system telnet was removed in High Sierra — install a replacement:

```bash
brew install telnet
```

On Linux, `telnet` is usually available from your distribution's package manager (`apt install telnet`, `dnf install telnet`, etc.). On Windows, PuTTY configured to raw telnet on port 4000 is the simplest path.

### Web Client

Open <https://game.gridwars.run> in any modern browser. The web client has full color support and does not require any installation.

### MUD Clients

Any MUD client works:

- **Mudlet** — recommended for advanced scripting and trigger support
- **TinTin++** — lightweight terminal-based, scriptable
- **MUSHclient** — Windows; reliable and widely documented
- **Blastwave** / **BeipMU** — modern cross-platform options

Connect each client to host `game.gridwars.run`, port `4000`, protocol raw telnet (not SSH).

### Creating an Account

Once connected you will see the GridWars login screen. Two commands create and access your character:

```
create <name> <password>
connect <name> <password>
```

Names are case-sensitive and unique. Passwords are never echoed. Pick something you will remember — there is no password-recovery flow yet.

---

## First Five Minutes

### You Land in Users' Sector

Every new character and every respawn starts here. Users' Sector is the Grid's arrival hall: rows of terminals glowing blue-white, spawn queues cycling, civilian programs moving in short bursts of light. You are safe to get your bearings.

Type `look` to render your surroundings. Type `scan` for a tactical view: which other programs are present, which exits are available, and a one-line flavor read on the sector.

### The Welcome Program

If a Welcome Program (Daemon-0001) is on patrol, it may acknowledge your arrival. Daemons are autonomous programs that move and engage on their own schedule. They are not aggressive by default, but they do patrol.

### Your Starter Disc

New characters begin unarmed. An administrator or a future in-world vendor will give you a standard Identity Disc. Once you have one, `inventory` shows it, and `equip <disc name>` slots it. Without an equipped disc, `strike` still works but at base damage only — no bonus, no cooldown.

### Choose Your Faction

The single most important early decision is faction. Type `faction` to see all three, then:

```
faction choose Users
faction choose Programs
faction choose Daemons
```

This is a one-shot decision. Faction changes require an admin override. Your choice tints how other players see you in `scan` output, affects themed combat broadcast text, and (on the roadmap) will gate sector access. Do not skip this step — the Grid will keep nudging you on every login until you align.

### Run Your First Scan

```
scan
```

This is the tactical heartbeat of the game. You will see faction-tinted player names, the current exits, and whether your faction controls this sector. Make it a reflex.

### Walk to the Combat Grid

The five sectors are connected in a fixed layout:

```
                    [Archive Node]
                          |
                       (west/east)
                          |
[Combat Grid] -- (south/north) -- [Daemon Gate] -- (west/east) -- [Lightcycle Causeway] -- (south/north) -- [Users' Sector]
```

From Users' Sector, the path to the Combat Grid is:

```
north    → Lightcycle Causeway
east     → Daemon Gate
north    → Combat Grid
```

Or type `n`, `e`, `n` using the short aliases. The Archive Node sits east of Users' Sector and west of nothing else — it is a dead end, good for quiet storage and lore.

Once you reach the Combat Grid, you are in the primary PvP arena. Type `scan` again: anyone here is a valid target. `strike <name>` to begin.

---

## Command Reference

Commands are grouped below by function. Aliases (if any) are shown in parentheses.

### Info Commands

---

**`status`**

Shows your identity disc HUD: name, current sector, faction, integrity (HP), energy, experience, and grid rank. Color codes indicate condition: green is healthy, yellow is a warning, red is critical.

```
status
```

Example output:
```
╔══════════ IDENTITY DISC ══════════╗
  Name      Rez
  Sector    Combat Grid
  Faction   Programs
  Integrity 100 / 100
  Energy     50 / 100
  Exp        45
  Rank       User
╚════════════════════════════════════╝
  Sectors  3 held by your faction
```

If you have a disc equipped, a `Disc` line shows the disc's current level and XP progress.

---

**`scan`**

Tactical sector view. Shows all other characters in your sector (faction-tinted), available exits, who controls the sector, and a one-line flavor description.

```
scan
```

Example output:
```
-- SECTOR SCAN: Combat Grid --
The arena floor is a flat plane of jet-black substrate...

Programs here:
  - Clu [Programs]
  - Flynn [Users]

Exits: south
Sector control: Daemons
```

`scan` reveals faction membership — yours and everyone else's. Use it before committing to a strike.

---

**`look`**

Re-renders the room description and its contents. Use this when you first arrive in a sector or want the full room prose rather than the tactical `scan` summary.

```
look
```

---

**`inventory` (`inv`)**

Lists everything you are carrying. Your equipped disc is marked `[equipped]`.

```
inventory
inv
```

---

**`who`**

Lists all currently connected players.

```
who
```

---

**`help <topic>`**

Built-in help system. `help gridwars` shows the curated GridWars command index. `help <command>` gives command-specific help.

```
help gridwars
help strike
help faction
```

---

### Combat Commands

---

**`strike <target>`**

Deals damage to another character in your current sector. You cannot strike across sectors or strike yourself.

```
strike Flynn
```

**Damage formula:** `BASE_DAMAGE(10) + random(0..5) + disc.damage_bonus`

Without an equipped disc, strikes deal 10–15 integrity of damage. With a level-1 standard disc (+5 bonus) they deal 15–20. With higher-level discs the bonus scales.

**Defeat:** When a target's integrity reaches 0, they are derezzed and respawned in Users' Sector with at least 25 integrity restored. Characters are never deleted. You gain 5 experience points on each victory.

**Cooldown:** When a disc is equipped, each strike starts a cooldown equal to the disc's `cooldown_seconds` (3 seconds for a standard disc). You cannot strike again until the cooldown expires.

---

**`challenge <target>`**

Sends a formal duel challenge to another character in your sector. The target has 30 seconds to respond. If they do not respond in time, the challenge expires automatically.

```
challenge Flynn
```

A target can only hold one pending challenge at a time. If you try to challenge someone who already has a pending challenge, you will be told so.

---

**`accept`**

Accepts a pending duel challenge directed at you. Both participants are immediately moved to a private DuelArena.

```
accept
```

---

**`decline`**

Declines a pending duel challenge. The challenger is notified.

```
decline
```

---

**`capture`**

Claims your current sector for your faction. You must be faction-aligned to use this. If your faction already holds the sector, this is a friendly no-op. Capturing a rival-held sector overwrites their ownership immediately.

```
capture
```

Sector ownership is visible in `scan` output and in `status` (as a count of sectors your faction holds).

---

**`equip <disc>`**

Equips an Identity Disc from your inventory. The disc must already be in your inventory. Equipping a new disc replaces the previously-equipped one (the old disc stays in inventory).

```
equip "Identity Disc"
equip razor-disc
```

---

**`unequip`**

Unequips your currently-equipped disc. The disc stays in inventory. Strikes fall back to base damage (no bonus, no cooldown) until you re-equip.

```
unequip
```

---

### Queue Commands

---

**`@queue duel` (`queue duel`)**

Joins the matchmaking queue. When two players are in the queue, the server pairs them into a duel automatically — no `challenge` step required.

```
@queue duel
```

---

**`@queue leave` (`queue leave`)**

Removes you from the matchmaking queue.

```
@queue leave
```

---

**`@queue status` (`@queue`, `queue status`)**

Shows current queue length and your position in it.

```
@queue
@queue status
```

---

### Movement Commands

---

**`north` (`n`), `south` (`s`), `east` (`e`), `west` (`w`)**

Move through named exits. Only exits that exist in the current sector are valid. `scan` lists available exits.

```
north
n
east
e
```

---

**`look`**

Re-renders the current sector. See [Info Commands](#info-commands) above.

---

### Social Commands

---

**`say <text>`**

Speaks aloud in your current sector. Everyone in the sector sees it.

```
say Is anyone watching the Combat Grid east exit?
```

---

**`pose <action>`** (sometimes `emote`)

Emotes an action visible to everyone in the sector.

```
pose examines the sector boundary, searching for an exit that isn't on any map.
```

---

**`who`**

Lists connected players. See [Info Commands](#info-commands) above.

---

**`quit`**

Disconnects from the Grid cleanly.

```
quit
```

---

### Faction Commands

---

**`faction`**

Lists all three factions with their taglines and descriptions, and shows your current alignment.

```
faction
```

---

**`faction choose <name>`**

Aligns yourself with a faction. Case-insensitive. Valid values: `Users`, `Programs`, `Daemons`. This is a one-shot decision — admin override is required to change it.

```
faction choose Programs
faction choose daemons
```

---

## Lightcycle Duel Mechanics

A duel is a structured first-to-three-strikes PvP match held in a private arena. Unlike an open `strike` in the Combat Grid, duels are consensual, isolated, and tracked.

### Starting a Duel: Challenge Flow

1. Both players must be in the same sector.
2. The challenger issues: `challenge <target>`
3. The target sees: `Rez has challenged you to a duel. Type accept or decline within 30s.`
4. The target types `accept` or `decline` within 30 seconds.
5. If no response arrives in 30 seconds, the challenge expires. Both parties are notified.

### Starting a Duel: Queue Flow

As an alternative to the challenge flow, either player can join the matchmaking queue with `@queue duel`. When two players are queued simultaneously, the server pairs them automatically into a duel without either player issuing a `challenge`. Use this when you want to fight anyone available rather than a specific opponent.

### Inside the Arena

Once a duel begins both characters are transported to a private **DuelArena** room. This room is created for the duel and destroyed afterward. No other players can enter.

Use `strike <opponent>` to fight. The same combat rules apply: base damage plus jitter plus disc bonus, cooldown enforced if a disc is equipped.

### Winning

The first player to land **3 successful strikes** wins the duel. On the third strike:

- The winner receives a victory message and gains experience.
- The loser receives a defeat message.
- Both players are returned to the sector they were in before the duel began.
- The arena is destroyed.

Note that defeat (integrity hitting 0 mid-duel) triggers the normal respawn flow before the strike count check — the character is moved to Users' Sector and their integrity is restored. The strike count check then still runs and the duel concludes cleanly.

### After the Duel

Post-duel ELO ratings update automatically (see [Rating and Leaderboard](#rating-and-leaderboard)). There is no cooldown between challenges — you can immediately issue or accept another.

### Summary

| Phase | Command | Notes |
|-------|---------|-------|
| Challenge | `challenge <target>` | Same sector; 30s timeout |
| Accept | `accept` | Teleports both to private arena |
| Decline | `decline` | Challenge cancelled; both notified |
| Fight | `strike <opponent>` | Standard combat rules apply |
| Queue alternative | `@queue duel` | Server pairs automatically |
| Win condition | — | First to 3 successful strikes |
| End | — | Return to pre-duel sector; arena deleted |

---

## Faction Lore

### Users

*"Uploaded. Underestimated."*

Users are civilian programs that arrived on the Grid the way most things arrive: by accident or necessity, with no preparation and no orientation. They are the default faction for every fresh sign-on, which means they are also the most numerous, the most disorganized, and the most consistently underestimated by the established power structures. In the early sessions after the Grid expanded, Users clustered in their sector out of simple unfamiliarity — they did not know what lay beyond the terminals. That changed. Users now have maps, coordination, and a growing suspicion that outnumbered does not mean outmatched.

In gameplay terms, Users are the starting faction. If you do not choose a faction, the Grid assumes you are one of them. There are no mechanical restrictions specific to Users, which means your combat effectiveness comes entirely from disc progression and player skill rather than any faction gate.

### Programs

*"Order is the throughput."*

Programs are the Grid's native architecture: structured processes with registered signatures, deterministic routines, and a long institutional memory. They built the lattice of sectors, established the exit geometry, and wrote most of the administrative code that still runs beneath everything. They are not conservative by ideology so much as by design — a Program that deviates from its registered function is, by definition, no longer quite a Program. They are deeply suspicious of unregistered processes and keep a running tally of which sectors belong to the Grid's original owners.

In gameplay terms, Programs are the faction for players who prefer a structured, tactical approach. Their sector-control ambitions make them natural organizers of coordinated pushes. The faction does not grant mechanical bonuses yet, but faction identity in `scan` output sends a clear signal about your intentions.

### Daemons

*"We are the noise in your stack."*

Daemons are what happens when a scheduled process slips the clock, runs outside its assigned window, and discovers that nobody is watching. Some are corrupted. Some were never valid to begin with. All of them have discovered that the Gap — the space between scheduled sectors — is more interesting than anything on the official map. Daemons do not patrol in straight lines. They do not recognize register ownership. They operate on the Grid the way signal noise operates in a transmission: present everywhere the architecture assumes they are not, and capable of drowning out legitimate traffic when they choose to coordinate.

In gameplay terms, Daemons are the faction for players who prefer chaos, fast aggression, and control of the Combat Grid and Daemon Gate. The faction's aesthetic is hostile — other players see Daemon-faction names in red — and the NPC Daemon patrols at Daemon Gate reflect their presence as a constant environmental hazard.

---

## Rating and Leaderboard

### How Ratings Work

Every player character starts with a rating of **1000**. After each duel, the winner's and loser's ratings update using the standard **ELO formula** with a K-factor of 32.

The expected score formula is:

```
E_winner = 1 / (1 + 10^((loser_rating - winner_rating) / 400))
```

The rating change is:

```
delta = 32 * (1 - E_winner)
winner_rating += delta
loser_rating  -= delta
```

Ratings are floored at 0 — they cannot go negative. An upset win (lower-rated player defeats higher-rated) produces a larger rating swing than a win against a weaker opponent. The system self-corrects quickly in an active player pool.

### Leaderboard

The `@leaderboard` command shows the top-rated players across all factions. Leaderboard rankings reset only if explicitly wiped by an administrator; they persist across sessions, logouts, and respawns.

> **Status note:** The `@leaderboard` command is planned for a near-term update and will be live shortly after launch. The ELO rating engine is already implemented.

---

## Disc XP and Leveling

Your Identity Disc grows stronger as you use it. Discs accumulate XP from combat and level from 1 to 5.

### XP Thresholds

| Level | XP Required | Damage Bonus |
|-------|-------------|--------------|
| L1    | 0           | +5           |
| L2    | 100         | +7           |
| L3    | 300         | +9           |
| L4    | 700         | +11          |
| L5    | 1500        | +13          |

XP is additive — reaching L2 requires 100 total XP from a fresh disc, L3 requires 300 total, and so on. Level 5 is the cap. XP continues to accumulate past the cap but the disc does not level further.

When your disc levels up while you have it equipped, you receive a notification.

### Damage with a Leveled Disc

At L5, a fully-leveled disc adds +13 to every strike. Combined with the base damage of 10–15 (base + random jitter), that puts each strike at 23–28 integrity per hit — before any future balance passes.

### Getting a Disc

New characters must obtain a disc from an administrator or in-world vendor. Use `inventory` to verify you have one, then `equip <disc name>` to slot it. A disc must be in your inventory to be equipped.

---

## FAQ

**How do I die?**

You cannot die permanently. When your integrity reaches 0 from any `strike`, you are "derezzed" — the room broadcasts a derezz message, and you are immediately moved back to Users' Sector with your integrity restored to at least 25. Your faction, experience, grid rank, and disc are all retained. Characters are never deleted.

---

**What happens if I disconnect mid-duel?**

If you disconnect during a duel, your character remains in the arena until the session times out and Evennia removes the puppet from the arena. The opponent's strikes against your character still count. If the opponent reaches 3 strikes before you reconnect, the duel ends in their favor and both characters are returned to their pre-duel sectors. Your character's rating updates as a loss. If you reconnect quickly enough, you can resume fighting.

---

**Can I switch factions?**

No, not without admin intervention. `faction choose` is a one-shot command. The Grid treats faction loyalty as a permanent code-level registration. If you have a compelling reason to switch (account error, new player regret), contact an administrator via the bug-report channel.

---

**Is the world persistent?**

Yes. The world runs continuously on a dedicated server at game.gridwars.run. Sectors, faction ownership, character stats, disc XP, and ratings all persist between sessions. There is no daily reset, no scheduled wipe, and no offline drift. What you build (sector control) and what you earn (experience, ratings, disc XP) stay until something in-game changes them.

---

**How do I report a bug?**

The codebase is open source at [github.com/jsgerman-oss/gridwars.run](https://github.com/jsgerman-oss/gridwars.run). File an issue there with a description of what happened, what you expected, and your character name + approximate timestamp. In-game you can also `say` to an admin if one is online — `who` shows connected players and admins are labeled.

---

**How do daemons work?**

Daemons (capital D) are NPC programs that patrol sectors autonomously. The initial Daemon-0001 spawns at Daemon Gate and patrols on a script cycle. Daemons sense non-Daemon characters in their sector and can engage them. They follow the same combat rules as player characters — they strike, deal damage, and can derezz you. Unlike player characters, Daemons are not persistent: if derezzed, they respawn from the patrol script. They are not a faction to join — they are environmental hazards that reinforce the Daemon Gate's lore as a hostile threshold.

---

**What is the difference between `strike` and `challenge`?**

`strike <target>` is an immediate, unconditional attack in your current sector. No consent required. Any character in your sector is a valid target. The fight happens in the open sector where bystanders can watch, intervene, or pile on.

`challenge <target>` initiates a formal duel. The target must `accept` before any combat begins. Once accepted, both players are moved to a private arena where only they can fight. The duel ends when one player lands 3 strikes; then both return to their previous locations. Duels update ELO ratings; open-sector strikes do not (ratings are duel-only).

---

**What does `scan` tell other players about me?**

`scan` shows other players that you are present in the sector, your character name, and your faction (color-coded). It does not reveal your integrity, energy, experience, rating, or equipped disc. Your location is always visible to sector-mates — there is no stealth mechanic yet.

---

**How do I get a new disc?**

Currently, discs are issued by administrators using the `@spawn_disc` admin command. When in-world vendors or drop mechanics ship (planned), you will be able to obtain discs through gameplay. For now: connect and ask an admin in-game, or watch the GitHub issues for vendor progress.

---

**What does `grid_rank` mean?**

`grid_rank` is a rank label displayed on your `status` HUD. All characters start at rank `User`. In future updates, grid rank will reflect progression milestones — faction leadership, combat record, or admin-awarded designations. For now it is a display field only. No mechanical gating is attached to it.

---

**What is `energy`?**

Energy is a stat on your identity disc HUD, currently displayed at a default of 50/100. It does not yet gate any commands — it is a reserved resource for future mechanics (ability costs, special moves). Think of it as a placeholder that future systems will consume.

---

**What happens in a draw / if both players reach 0 integrity simultaneously?**

The defeat flow fires on the target of the successful strike first. The attacker's integrity check runs after the target's. In practice, both cannot reach 0 simultaneously from a single strike — strikes resolve sequentially. If a future mechanic produces simultaneous defeat, the duel's `end_arena` function handles cleanup regardless by returning everyone to their origins.

---

**Is there a global chat channel?**

Not yet. `say` is sector-local. There is no global shout, OOC channel, or cross-sector communication built in yet. Future updates may add a channel system via Evennia's built-in channel framework. For now: move to the same sector as someone to talk to them.

---

*This guide reflects the current state of the GridWars.run codebase. As new mechanics ship, this document is updated. For the changelog, see [CHANGELOG.md](../CHANGELOG.md) in the repo root, or watch the [GitHub releases](https://github.com/jsgerman-oss/gridwars.run/releases).*
