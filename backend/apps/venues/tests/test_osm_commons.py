from io import BytesIO, StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from PIL import Image

from apps.venues.management.commands import add_commons_photos as commons
from apps.venues.management.commands import import_osm_venues as osm
from apps.venues.models import EventType, Venue

User = get_user_model()

ELEMENTS = [
    {"type": "node", "id": 1, "lat": 9.01, "lon": 38.76,
     "tags": {"tourism": "hotel", "name": "Sheraton Addis", "stars": "5", "phone": "+251 11 517 1717"}},
    {"type": "way", "id": 2, "center": {"lat": 9.0, "lon": 38.78},
     "tags": {"amenity": "events_venue", "name": "Millenium Hall", "addr:suburb": "Bole"}},
    {"type": "node", "id": 3, "lat": 9.02, "lon": 38.75, "tags": {"tourism": "hotel", "name": "3F furniture factory"}},
    {"type": "node", "id": 4, "lat": 9.02, "lon": 38.75, "tags": {"tourism": "hotel"}},  # no name
]


def jpeg_bytes():
    buf = BytesIO()
    Image.new("RGB", (40, 30), "orange").save(buf, "JPEG")
    return buf.getvalue()


class OsmImportTests(TestCase):
    def setUp(self):
        for slug in ["wedding", "conference", "corporate-meeting", "holiday-party", "birthday", "graduation"]:
            EventType.objects.create(name=slug, slug=slug)
        User.objects.create_user("owner@demo.yetyideges.test", "x-Strong-pass-77", role="owner")

    def run_import(self, *args):
        out = StringIO()
        with mock.patch.object(osm, "fetch_overpass", return_value=ELEMENTS):
            call_command("import_osm_venues", *args, stdout=out)
        return out.getvalue()

    def test_import(self):
        out = self.run_import()
        self.assertIn("Imported 2 new", out)
        names = list(Venue.objects.order_by("name").values_list("name", flat=True))
        self.assertEqual(names, ["Millenium Hall", "Sheraton Addis"])  # factory + unnamed dropped
        hall = Venue.objects.get(osm_id="way/2")
        self.assertEqual((hall.source, hall.area, hall.details_estimated), ("osm", "Bole", True))
        sheraton = Venue.objects.get(osm_id="node/1")
        self.assertIn("+251 11 517 1717", sheraton.description)
        self.assertEqual(sheraton.capacity_max, 800)  # 5-star hotel profile
        self.assertIn("Imported 0 new, updated 2", self.run_import())


class CommonsPhotoTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user("o@x.test", "x-Strong-pass-77", role="owner")
        self.hotel = Venue.objects.create(owner=owner, name="Sheraton Addis", description="d", city="Addis Ababa",
                                          capacity_min=1, capacity_max=10, price_per_day=1, source="osm",
                                          osm_id="node/1", tagline="5-star hotel")
        self.hall = Venue.objects.create(owner=owner, name="Made Up Hall", description="d", city="Addis Ababa",
                                         capacity_min=1, capacity_max=10, price_per_day=1)

    def fake_search(self, query, limit=12):
        file = lambda title: {"title": f"File:{title}", "url": f"https://upload.example/{title}",
                              "page": f"https://commons.example/{title}", "author": "A. Photographer",
                              "licence": "CC BY-SA 4.0"}
        if query.startswith("Sheraton Addis"):
            return [file("Sheraton Addis Ababa lobby.jpg")]
        return [file(f"{query}.jpg")]

    def test_real_photo_when_title_matches_else_illustrative(self):
        out = StringIO()
        with mock.patch.object(commons, "search_files", side_effect=self.fake_search), \
             mock.patch.object(commons, "_open", return_value=jpeg_bytes()):
            call_command("add_commons_photos", stdout=out)
        real = self.hotel.photos.get()
        self.assertFalse(real.is_illustrative)
        self.assertIn("CC BY-SA 4.0", real.credit)
        self.assertTrue(real.image.name.endswith(".webp"))
        self.assertTrue(self.hall.photos.get().is_illustrative)
        self.assertIn("1 of the actual venue, 1 illustrative", out.getvalue())

    def test_matching_and_filters(self):
        self.assertTrue(commons.matches_venue("File:Sheraton Addis Ababa.jpg", "Sheraton Addis"))
        self.assertFalse(commons.matches_venue("File:Sheraton Dubai.jpg", "Sheraton Addis"))
        self.assertTrue(commons.OLD_PHOTO.search("wedding 1909.jpg"))
        self.assertFalse(commons.OLD_PHOTO.search("IMG_20190912.jpg"))


class GenericPhotoFilterTests(TestCase):
    def test_rejects_real_places_people_and_documents(self):
        venues = ["Sheraton Addis", "Hilton Addis Ababa", "Golden Tulip"]
        bad = [
            "File:Sheraton Hotel, Addis Ababa (2058298419).jpg",
            "File:Omar al-Bashir, 12th AU Summit, 090202-N-0506A-724.jpg",
            "File:Notepaper from the Ras Hotel, Addis Ababa.jpg",
            "File:Bud Uanna ADDIS ABABA Tenastelin p.10.jpg",
            "File:Sun Picture Gardens, Chinatown Precinct, Broome Western Australia.jpg",
            "File:Layout of a table in the Nobel Prize for the banquet at the City Hall.jpg",
        ]
        good = ["File:Banquet Room interior, Brother Hotel 20130212.jpg", "File:Vietnamese wedding reception.jpg"]
        self.assertEqual([commons.is_generic(t, venues) for t in bad], [False] * len(bad))
        self.assertEqual([commons.is_generic(t, venues) for t in good], [True, True])
