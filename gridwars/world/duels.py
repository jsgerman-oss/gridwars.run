"""
GridWars.run duel lifecycle helpers — create/end the arena, move
participants in/out, restore origin rooms on completion.
"""
from datetime import datetime, timezone

from evennia.objects.models import ObjectDB
from evennia.utils.create import create_object


def create_arena(challenger, defender):
    """Create a DuelArena, move both characters in, remember origins.

    Args:
        challenger: Character object initiating the duel.
        defender:   Character object accepting the duel.

    Returns:
        DuelArena: the newly created arena Room.
    """
    arena = create_object(
        "typeclasses.duel_arenas.DuelArena",
        key=f"Duel: {challenger.key} vs {defender.key}",
    )
    arena.tags.add("duel-arena", category="ephemeral")
    arena.participants = [challenger.id, defender.id]
    arena.origins = {
        str(challenger.id): challenger.location.id if challenger.location else None,
        str(defender.id): defender.location.id if defender.location else None,
    }
    arena.started_at = datetime.now(timezone.utc).isoformat()
    challenger.move_to(arena, quiet=True)
    defender.move_to(arena, quiet=True)
    return arena


def end_arena(arena, winner=None):
    """Move participants back to their origins and destroy the arena.

    Args:
        arena:  DuelArena Room to tear down.
        winner: (optional) winning Character object. Stored on arena
                before deletion so callers can read it before calling
                this function. Not required (LD3 populates winner_id).
    """
    for char_id_str, origin_id in (arena.origins or {}).items():
        try:
            char = ObjectDB.objects.get(id=int(char_id_str))
        except ObjectDB.DoesNotExist:
            continue
        if origin_id:
            try:
                origin = ObjectDB.objects.get(id=origin_id)
            except ObjectDB.DoesNotExist:
                origin = None
            if origin:
                char.move_to(origin, quiet=True)
    if winner:
        arena.winner_id = winner.id
    arena.delete()
