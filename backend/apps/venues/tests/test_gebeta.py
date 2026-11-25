from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.venues import gebeta
from apps.venues.management.commands.import_gebeta_places import looks_like_venue
from apps.venues.models import EventType, Venue

User = get_user_model()


def gp(pid, name, lat=9.0050, lng=38.7600, category="establishment", hood="OLYMPIA"):
    return gebeta.GebetaPlace(id=pid, name=name, display_name=f"{name}, Addis Ababa, Ethiopia",
                              category=category, latitude=lat, longitude=lng, city="Addis Ababa",
                              neighborhood=hood)


RESULTS = {
    "wedding hall": [gp("g1", "Sheger Wedding Hall"), gp("g2", "Bole Road", category="street")],
    "hotel": [gp("g1", "Sheger Wedding Hall"), gp("g3", "Kuriftu Hotel", 8.99, 38.79, hood="BOLE")],
    "garden": [gp("g4", "Garden Pharmacy", category="Store"), gp("g5", "Entoto Park Garden", 9.08, 38.76)],
}


def fake_search(query, bbox=None, limit=10):
    # only answer for the first grid box, so results aren't multiplied per box
    if bbox != next(gebeta.grid(n=1)):
        return []
    return RESULTS.get(query, [])


@override_settings(GEBETA_API_KEY="test-key")
class GebetaImportTests(TestCase):
    def setUp(self):
        for slug in ["wedding", "holiday-party", "conference", "corporate-meeting"]:
            EventType.objects.create(name=slug.title(), slug=slug)
        User.objects.create_user("owner@demo.yetyideges.test", "x-Strong-pass-77", role="owner")

    def run_import(self, *args):
        out = StringIO()
        with mock.patch.object(gebeta, "search", side_effect=fake_search):
            call_command("import_gebeta_places", "--grid", "1", *args, stdout=out)
        return out.getvalue()

    def test_filter(self):
        self.assertTrue(looks_like_venue(gp("x", "ሸገር አዳራሽ")))
        self.assertFalse(looks_like_venue(gp("x", "Bole Road", category="street")))
        self.assertFalse(looks_like_venue(gp("x", "Abebe Shop")))
        self.assertFalse(looks_like_venue(gp("x", "Garden Pharmacy", category="Store")))

    def test_import_dedupes_and_labels(self):
        self.run_import()
        names = set(Venue.objects.values_list("name", flat=True))
        self.assertEqual(names, {"Sheger Wedding Hall", "Kuriftu Hotel", "Entoto Park Garden"})
        v = Venue.objects.get(gebeta_id="g1")
        self.assertEqual((v.source, v.details_estimated, v.area), ("gebeta", True, "Olympia"))
        self.assertIn("conference", set(v.event_types.values_list("slug", flat=True)))  # from 'hotel' query
        self.assertEqual(Venue.objects.get(gebeta_id="g3").area, "Bole")

    def test_rerun_updates_and_skips_existing_same_place(self):
        owner = User.objects.get(email="owner@demo.yetyideges.test")
        # Already imported from Google, ~50 m away with the same name: must not duplicate.
        Venue.objects.create(owner=owner, name="Kuriftu Hotel", description="d", city="Addis Ababa",
                             capacity_min=1, capacity_max=10, price_per_day=1,
                             latitude="8.990400", longitude="38.790100", source="google")
        out = self.run_import()
        self.assertIn("skipped 1", out)
        self.assertEqual(Venue.objects.filter(name="Kuriftu Hotel").count(), 1)
        out = self.run_import()
        self.assertIn("Imported 0 new, updated 2, skipped 1", out)

    def test_dry_run_saves_nothing(self):
        out = self.run_import("--dry-run")
        self.assertIn("Sheger Wedding Hall", out)
        self.assertEqual(Venue.objects.count(), 0)

    def test_grid_covers_bbox(self):
        boxes = list(gebeta.grid(n=3))
        self.assertEqual(len(boxes), 9)
        self.assertEqual((boxes[0][0], boxes[0][1]), gebeta.ADDIS_ABABA_BBOX[:2])
        self.assertEqual((boxes[-1][2], boxes[-1][3]), gebeta.ADDIS_ABABA_BBOX[2:])
