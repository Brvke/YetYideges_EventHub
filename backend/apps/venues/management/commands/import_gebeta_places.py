"""Import event venues in Addis Ababa from Gebeta Maps (demo data).

    python manage.py import_gebeta_places --dry-run    # preview, saves nothing
    python manage.py import_gebeta_places              # import / update
    python manage.py import_gebeta_places --grid 2     # fewer API calls (2×2 boxes)

Needs GEBETA_API_KEY in .env (free Developer plan at https://gebeta.app).
API calls per run = number of queries × grid² (default 10 × 9 = 90).

Gebeta returns name, location, category and neighbourhood only, so imported
venues have no photos and get placeholder price/capacity (`details_estimated`).
Venues already in the database under the same name nearby (for example from a
Google import) are skipped rather than duplicated.
"""
import math
import re
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.venues import gebeta
from apps.venues.models import EventType, Venue

from .import_google_places import CITY, Command as GoogleCommand, Profile, guess_area

QUERIES = [
    Profile("wedding hall", ("wedding", "holiday-party"), (100, 600), 90000),
    Profile("event hall", ("wedding", "birthday", "holiday-party"), (50, 400), 60000),
    Profile("አዳራሽ", ("wedding", "birthday", "graduation"), (50, 400), 60000),
    Profile("banquet", ("wedding", "graduation", "holiday-party"), (100, 500), 75000),
    Profile("hotel", ("wedding", "conference", "corporate-meeting", "holiday-party"), (50, 500), 100000),
    Profile("resort", ("wedding", "corporate-meeting", "conference"), (50, 400), 90000),
    Profile("conference center", ("conference", "corporate-meeting"), (30, 400), 45000),
    Profile("garden", ("wedding", "birthday", "graduation", "baby-shower"), (30, 350), 55000),
    Profile("lounge", ("birthday", "holiday-party"), (20, 120), 30000),
    Profile("meeting room", ("corporate-meeting",), (5, 60), 12000),
]

# A result must look like a venue by name or category; this drops streets,
# neighbourhoods and unrelated shops that match a word like "garden".
VENUE_WORDS = re.compile(
    r"hall|hotel|resort|lounge|garden|conference|convention|cent(er|re)|venue|event|banquet|"
    r"ballroom|pavilion|club|አዳራሽ|ሆቴል|ሪዞርት|ማዕከል",
    re.IGNORECASE,
)
NOT_VENUE_CATEGORIES = {"country", "region", "place", "locality", "neighborhood", "street", "address"}
NOT_VENUE_WORDS = re.compile(
    r"pharmac|clinic|hospital|health|school|college|universit|church|mosque|bank|"
    r"supermarket|shop|store|garage|condominium|office|bureau|ministry|police|station",
    re.IGNORECASE,
)


def looks_like_venue(p: gebeta.GebetaPlace) -> bool:
    if not p.name or p.latitude is None or p.longitude is None:
        return False
    if p.category.lower() in NOT_VENUE_CATEGORIES or NOT_VENUE_WORDS.search(f"{p.name} {p.category}"):
        return False
    return bool(VENUE_WORDS.search(p.name) or VENUE_WORDS.search(p.category))


def metres_apart(lat1, lng1, lat2, lng2) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9ሀ-፿]", "", name.lower())


class Command(BaseCommand):
    help = "Import Addis Ababa event venues from Gebeta Maps (demo data)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="List results without saving")
        parser.add_argument("--limit", type=int, default=80, help="Max venues to import (default 80)")
        parser.add_argument("--grid", type=int, default=3, help="Split Addis into N×N search boxes (default 3)")

    def handle(self, *args, dry_run=False, limit=80, grid=3, **opts):
        if not settings.GEBETA_API_KEY:
            raise CommandError("GEBETA_API_KEY is not set in .env")
        grid = max(1, min(grid, 5))
        calls = len(QUERIES) * grid * grid
        self.stdout.write(f"Searching {CITY} with {calls} Gebeta API calls...")
        try:
            found = self.search(grid)
        except gebeta.GebetaError as exc:
            raise CommandError(str(exc))

        picked = list(found.values())[:limit]
        self.stdout.write(f"Found {len(found)} venue-like places; using {len(picked)}.")
        if dry_run:
            for place, profiles in picked:
                area = self.area(place)
                self.stdout.write(f"  - {place.name}  [{area or '?'} · {place.category or '-'}]")
            return
        created, updated, skipped = self.save(picked)
        self.stdout.write(self.style.SUCCESS(
            f"Imported {created} new, updated {updated}, skipped {skipped} already listed."))

    # ------------------------------------------------------------------------
    def search(self, n):
        found: dict[str, tuple[gebeta.GebetaPlace, list[Profile]]] = {}
        for profile in QUERIES:
            kept = 0
            for box in gebeta.grid(n=n):
                for place in gebeta.search(profile.query, bbox=box):
                    if not looks_like_venue(place):
                        continue
                    key = place.id or f"{norm(place.name)}@{place.latitude:.4f},{place.longitude:.4f}"
                    if key not in found:
                        found[key] = (place, [])
                        kept += 1
                    found[key][1].append(profile)
            self.stdout.write(f"  '{profile.query}': {kept} new venues")
        return found

    @staticmethod
    def area(place: gebeta.GebetaPlace) -> str:
        return guess_area(place.display_name) or place.neighborhood.title()

    def duplicate_of(self, place) -> Venue | None:
        """An existing venue with the same name within 300 m (e.g. from Google)."""
        target = norm(place.name)
        nearby = Venue.objects.filter(
            latitude__range=(place.latitude - 0.003, place.latitude + 0.003),
            longitude__range=(place.longitude - 0.003, place.longitude + 0.003),
        )
        for v in nearby:
            if norm(v.name) == target and metres_apart(
                place.latitude, place.longitude, float(v.latitude), float(v.longitude)
            ) <= 300:
                return v
        return None

    @transaction.atomic
    def save(self, picked):
        owner = GoogleCommand().import_owner()
        types = {t.slug: t for t in EventType.objects.all()}
        created = updated = skipped = 0
        for place, profiles in picked:
            fields = dict(
                name=place.name[:120],
                address=place.display_name[:200],
                city=CITY,
                area=self.area(place)[:120],
                latitude=Decimal(str(round(place.latitude, 6))),
                longitude=Decimal(str(round(place.longitude, 6))),
            )
            venue = Venue.objects.filter(gebeta_id=place.id).first() if place.id else None
            if venue:
                for k, v in fields.items():
                    setattr(venue, k, v)
                venue.save()
                updated += 1
            elif self.duplicate_of(place):
                skipped += 1
                continue
            else:
                lo, hi = max((p.capacity for p in profiles), key=lambda c: c[1])
                where = f"{fields['area']}, {CITY}" if fields["area"] else CITY
                venue = Venue.objects.create(
                    owner=owner,
                    source=Venue.Source.GEBETA,
                    gebeta_id=place.id or None,
                    tagline=(place.category.title() if place.category and place.category != "establishment"
                             else "Event venue")[:160],
                    description=(f"Event venue in {where}.\n\nThis is a demo listing imported from Gebeta Maps. "
                                 "The name and location come from Gebeta; price and capacity are estimates."),
                    capacity_min=lo,
                    capacity_max=hi,
                    price_per_day=max(p.price for p in profiles),
                    details_estimated=True,
                    rental_policies="Demo listing imported from Gebeta Maps. Contact the venue directly "
                                    "to confirm prices, capacity and policies.",
                    **fields,
                )
                created += 1
            slugs = {s for p in profiles for s in p.event_types}
            venue.event_types.add(*[types[s] for s in slugs if s in types])
        return created, updated, skipped
