"""Unit tests for the ownership data layer (gridwars/world/ownership.py)."""
from evennia.utils.test_resources import EvenniaTest
from evennia.utils.create import create_object

from world.ownership import get_owner, set_owner, clear_owner, rooms_owned_by


class OwnershipTestCase(EvenniaTest):

    def setUp(self):
        super().setUp()
        self.room = create_object("evennia.objects.objects.DefaultRoom", key="TestSector")

    def test_unclaimed_returns_none(self):
        self.assertIsNone(get_owner(self.room))

    def test_set_owner_then_get(self):
        set_owner(self.room, "Users")
        self.assertEqual(get_owner(self.room), "Users")

    def test_set_owner_replaces_prior(self):
        set_owner(self.room, "Users")
        set_owner(self.room, "Daemons")
        self.assertEqual(get_owner(self.room), "Daemons")

    def test_clear_owner(self):
        set_owner(self.room, "Programs")
        clear_owner(self.room)
        self.assertIsNone(get_owner(self.room))

    def test_rooms_owned_by(self):
        room2 = create_object("evennia.objects.objects.DefaultRoom", key="TestSector2")
        set_owner(self.room, "Users")
        set_owner(room2, "Users")
        owned = rooms_owned_by("Users")
        self.assertEqual(len(owned), 2)
        self.assertIn(self.room, owned)
        self.assertIn(room2, owned)

    def test_clear_owner_on_unclaimed_room_is_noop(self):
        # Should not raise
        clear_owner(self.room)
        self.assertIsNone(get_owner(self.room))
