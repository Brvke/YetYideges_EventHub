from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.venues import google
from apps.venues.models import EventType, Venue

User = get_user_model()


def place(pid, name, address="Bole Road, Addis Ababa, Ethiopia", operational=True):
    return google.PlaceResult(
        place_id=pid, name=name, address=address, latitude=9.0, longitude=38.78,
        types=["event_venue"], type_label="Event venue", summary="", maps_url=f"https://maps.google.com/?cid={pid}",
        operational=operational,
    )


def fake_search(query, max_pages=2, **kw):
    if query.startswith("wedding hall"):
        return iter([place("p1", "Grand Hall"), place("p2", "Closed Hall", operational=False)])
    if query.startswith("conference hall"):
        return iter([place("p1", "Grand Hall"), place("p3", "Kazanchis Centre", "Kazanchis, Addis Ababa")])
    return iter([])


@override_settings(GOOGLE_MAPS_API_KEY="test-key")
class ImportGooglePlacesTests(APITestCase):
    def setUp(self):
        for slug in ["wedding", "holiday-party", "conference", "corporate-meeting"]:
            EventType.objects.create(name=slug.title(), slug=slug)
        User.objects.create_user("owner@demo.yetyideges.test", "x-Strong-pass-77", role="owner")

    def run_import(self, *args):
        out = StringIO()
        with mock.patch.object(google, "search_text", side_effect=fake_search):
            call_command("import_google_places", *args, stdout=out)
        return out.getvalue()

    def test_import_merges_duplicates_and_skips_closed(self):
        self.run_import()
        self.assertEqual(Venue.objects.count(), 2)
        grand = Venue.objects.get(google_place_id="p1")
        # found by both the wedding and conference queries
        self.assertEqual(
            set(grand.event_types.values_list("slug", flat=True)),
            {"wedding", "holiday-party", "conference", "corporate-meeting"},
        )
        self.assertEqual((grand.source, grand.details_estimated, grand.area), ("google", True, "Bole"))
        self.assertEqual(Venue.objects.get(google_place_id="p3").area, "Kazanchis")

    def test_rerun_updates_instead_of_duplicating(self):
        self.run_import()
        v = Venue.objects.get(google_place_id="p1")
        v.price_per_day = 123
        v.save()
        out = self.run_import()
        self.assertIn("Imported 0 new and updated 2", out)
        self.assertEqual(Venue.objects.get(google_place_id="p1").price_per_day, 123)

    def test_dry_run_saves_nothing(self):
        out = self.run_import("--dry-run")
        self.assertIn("Grand Hall", out)
        self.assertEqual(Venue.objects.count(), 0)


class GooglePhotoProxyTests(APITestCase):
    def setUp(self):
        owner = User.objects.create_user("o@x.test", "x-Strong-pass-77", role="owner")
        self.venue = Venue.objects.create(
            owner=owner, name="Grand Hall", description="d", city="Addis Ababa",
            capacity_min=1, capacity_max=100, price_per_day=1, google_place_id="p1", source="google",
        )
        self.photos = [{"name": "places/p1/photos/a", "width": 10, "height": 10,
                        "attributions": [{"name": "Abebe", "url": "https://maps.google.com/u/1"}]}]

    def test_list_cover_points_to_proxy(self):
        r = self.client.get("/api/venues/")
        self.assertTrue(r.data["results"][0]["cover_photo"].endswith("/api/venues/grand-hall/google-photo/0/"))

    def test_proxy_redirects_to_fresh_google_url(self):
        with mock.patch.object(google, "place_photos", return_value=self.photos), \
             mock.patch.object(google, "photo_url", return_value="https://lh3.googleusercontent.com/x"):
            r = self.client.get("/api/venues/grand-hall/google-photo/0/")
            self.assertEqual((r.status_code, r["Location"]), (302, "https://lh3.googleusercontent.com/x"))
            self.assertEqual(self.client.get("/api/venues/grand-hall/google-photo/5/").status_code, 404)
            data = self.client.get("/api/venues/grand-hall/google-photos/").data
        self.assertEqual(data["photos"][0]["attributions"][0]["name"], "Abebe")

    def test_owner_editing_price_clears_estimate_flag(self):
        self.venue.details_estimated = True
        self.venue.save()
        self.client.force_authenticate(self.venue.owner)
        self.client.patch(f"/api/owner/venues/{self.venue.id}/", {"price_per_day": "50000"}, format="json")
        self.venue.refresh_from_db()
        self.assertFalse(self.venue.details_estimated)
