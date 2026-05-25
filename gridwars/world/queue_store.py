"""
Persistent duel queue storage backed by ServerConfig.

Uses ServerConfig.objects.conf() so the queue survives `evennia reload`.
Values are plain lists of character `.id` integers.

Public API (consumed by commands.queue and world.matchmaking):
  get_queue()          -> list[int]
  enqueue(char_id)     -> bool  (True = added, False = already present)
  dequeue(char_id)     -> bool  (True = removed, False = not present)
  clear_queue()        -> None
"""

from evennia.server.models import ServerConfig

_QUEUE_KEY = "gw_duel_queue"


def get_queue() -> list:
    """Return the current duel queue as a list of character id ints."""
    return list(ServerConfig.objects.conf(_QUEUE_KEY, default=list) or [])


def enqueue(char_id: int) -> bool:
    """
    Add char_id to the queue if not already present.

    Returns True if the character was added, False if already queued.
    """
    queue = get_queue()
    if char_id in queue:
        return False
    queue.append(char_id)
    ServerConfig.objects.conf(_QUEUE_KEY, value=queue)
    return True


def dequeue(char_id: int) -> bool:
    """
    Remove char_id from the queue if present.

    Returns True if removed, False if char_id was not in the queue.
    """
    queue = get_queue()
    if char_id not in queue:
        return False
    queue.remove(char_id)
    ServerConfig.objects.conf(_QUEUE_KEY, value=queue)
    return True


def clear_queue() -> None:
    """Wipe the queue. Intended for testing and admin resets."""
    ServerConfig.objects.conf(_QUEUE_KEY, value=[])
