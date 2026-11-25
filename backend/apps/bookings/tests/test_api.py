from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.bookings.models import Booking
from apps.reviews.models import Review
from apps.venues.models import BlockedDate, Venue

User = get_user_model()
PW = "a-Strong-test-pass-91"


class BookingFlowTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner@x.test", PW, role="owner", first_name="O")
        self.guest = User.objects.create_user("guest@x.test", PW, first_name="Abebe", last_name="Kebede")
        self.guest2 = User.objects.create_user("guest2@x.test", PW)
        self.venue = Venue.objects.create(
            owner=self.owner, name="Test Hall", description="d", city="Addis Ababa",
            capacity_min=10, capacity_max=100, price_per_day=5000,
        )
        self.day = timezone.localdate() + timedelta(days=10)

    def request(self, user, **extra):
        self.client.force_authenticate(user)
        data = {"venue": self.venue.slug, "event_date": self.day, "guest_count": 50, **extra}
        return self.client.post("/api/bookings/", data, format="json")

    def test_guest_can_request_and_price_is_quoted(self):
        r = self.request(self.guest)
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "pending")
        self.assertEqual(r.data["quoted_price"], "5000.00")

    def test_capacity_and_past_date_rejected(self):
        self.assertEqual(self.request(self.guest, guest_count=500).status_code, 400)
        r = self.request(self.guest, event_date=timezone.localdate() - timedelta(days=1))
        self.assertEqual(r.status_code, 400)

    def test_blocked_date_rejected(self):
        BlockedDate.objects.create(venue=self.venue, date=self.day)
        self.assertEqual(self.request(self.guest).status_code, 400)

    def test_accept_declines_competitors_and_locks_the_date(self):
        b1 = self.request(self.guest).data["id"]
        b2 = self.request(self.guest2).data["id"]

        self.client.force_authenticate(self.owner)
        r = self.client.post(f"/api/owner/bookings/{b1}/accept/", {"note": "See you!"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(Booking.objects.get(pk=b2).status, "declined")

        # the date now shows as unavailable and new requests are refused
        avail = self.client.get(f"/api/venues/{self.venue.slug}/availability/").data
        self.assertIn(self.day, avail["unavailable"])
        self.assertEqual(self.request(User.objects.create_user("g3@x.test", PW)).status_code, 400)

    def test_database_blocks_double_booking(self):
        Booking.objects.create(venue=self.venue, guest=self.guest, event_date=self.day,
                               guest_count=20, quoted_price=1, status="accepted")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(venue=self.venue, guest=self.guest2, event_date=self.day,
                                   guest_count=20, quoted_price=1, status="accepted")

    def test_only_owner_role_can_manage(self):
        b = self.request(self.guest).data["id"]
        r = self.client.post(f"/api/owner/bookings/{b}/accept/")  # still the guest
        self.assertEqual(r.status_code, 403)
        other_owner = User.objects.create_user("o2@x.test", PW, role="owner")
        self.client.force_authenticate(other_owner)
        self.assertEqual(self.client.post(f"/api/owner/bookings/{b}/accept/").status_code, 404)

    def test_guest_cancel(self):
        b = self.request(self.guest).data["id"]
        r = self.client.post(f"/api/bookings/{b}/cancel/")
        self.assertEqual(r.data["status"], "cancelled")


class ReviewTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner@x.test", PW, role="owner")
        self.guest = User.objects.create_user("guest@x.test", PW, first_name="Abebe", last_name="Kebede")
        self.venue = Venue.objects.create(
            owner=self.owner, name="Garden", description="d", city="Addis Ababa",
            capacity_min=1, capacity_max=100, price_per_day=100,
        )

    def booking(self, days, status="accepted"):
        return Booking.objects.create(
            venue=self.venue, guest=self.guest, event_date=timezone.localdate() + timedelta(days=days),
            guest_count=10, quoted_price=100, status=status,
        )

    def test_review_after_event_updates_rating(self):
        b = self.booking(-3)
        self.client.force_authenticate(self.guest)
        r = self.client.post("/api/reviews/", {"booking": b.id, "rating": 4, "comment": "Nice"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["author_name"], "Abebe K.")
        self.venue.refresh_from_db()
        self.assertEqual((self.venue.rating_count, float(self.venue.rating_avg)), (1, 4.0))

        # one review per booking
        r = self.client.post("/api/reviews/", {"booking": b.id, "rating": 5}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_cannot_review_future_or_unconfirmed(self):
        self.client.force_authenticate(self.guest)
        for b in (self.booking(5), self.booking(-5, status="declined")):
            r = self.client.post("/api/reviews/", {"booking": b.id, "rating": 5}, format="json")
            self.assertEqual(r.status_code, 400)

    def test_owner_can_reply(self):
        b = self.booking(-1)
        review = Review.objects.create(booking=b, venue=self.venue, author=self.guest, rating=5)
        self.client.force_authenticate(self.owner)
        r = self.client.post(f"/api/owner/reviews/{review.id}/reply/", {"owner_reply": "Thank you!"})
        self.assertEqual(r.data["owner_reply"], "Thank you!")


class SearchTests(APITestCase):
    def setUp(self):
        owner = User.objects.create_user("owner@x.test", PW, role="owner")
        mk = lambda **kw: Venue.objects.create(owner=owner, description="d", city="Addis Ababa", **kw)
        mk(name="Entoto Wedding Garden", capacity_min=50, capacity_max=500, price_per_day=80000)
        mk(name="Bole Meeting Room", capacity_min=5, capacity_max=30, price_per_day=10000)

    def names(self, **params):
        return [v["name"] for v in self.client.get("/api/venues/", params).data["results"]]

    def test_filters(self):
        self.assertEqual(self.names(q="weddings"), ["Entoto Wedding Garden"])  # stemmed
        self.assertEqual(self.names(q="ento"), ["Entoto Wedding Garden"])      # partial word
        self.assertEqual(self.names(guests=20), ["Bole Meeting Room"])
        self.assertEqual(self.names(max_price=20000), ["Bole Meeting Room"])
