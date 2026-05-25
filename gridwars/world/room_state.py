"""
GridWars.run room-state helpers.

Provides a thin, importable API over room-level DB attributes so that
consumers (repop ticker, tests, combat commands) never read raw
`room.db.*` keys directly.

Currently tracks one flag:
    combat_active (bool) — True while at least one PvE fight is in
    progress in this room, or while a duel arena is live. The Epic 19
    repop ticker reads this to skip rooms mid-fight.

Attribute lifecycle:
    Set:   CmdStrike.func() when the target is a Daemon-faction character.
           DuelArena.at_object_receive() when a duel participant enters.
    Clear: CmdStrike._defeat() on daemon kill.
           Room.at_object_leave() when the last player-account leaves.
           DuelArena teardown (world.duels.end_arena) via
           clear_combat_active().
"""


def is_room_in_combat(room) -> bool:
    """Return True if *room* has an active combat flag set.

    Args:
        room: Any Evennia room object (or None).

    Returns:
        bool: True when ``room.db.combat_active`` is truthy, False otherwise
              (including when *room* is None or the attribute is missing).
    """
    if room is None:
        return False
    return bool(room.db.combat_active)


def set_combat_active(room) -> None:
    """Mark *room* as having an active combat.

    Args:
        room: Evennia room object. No-op when None.
    """
    if room is None:
        return
    room.db.combat_active = True


def clear_combat_active(room) -> None:
    """Clear the combat-active flag on *room*.

    Safe to call redundantly (idempotent). Also safe when *room* is None.

    Args:
        room: Evennia room object. No-op when None.
    """
    if room is None:
        return
    room.db.combat_active = False
