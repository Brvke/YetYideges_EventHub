"""Import event venues in Addis Ababa from the Google Places API (New).

    python manage.py import_google_places --dry-run     # show what would be imported
    python manage.py import_google_places               # import / update
    python manage.py import_google_places --limit 40    # cap the number of venues
    python manage.py import_google_places --refresh     # re-sync stored venues from Google

Intended for demo/testing data. Price and capacity are not in Google's data, so
imported venues get placeholder values by venue type and `details_estimated=True`
(the UI labels them). Photos are never downloaded; see apps/venues/google.py.

Needs GOOGLE_MAPS_API_KEY in .env with the "Places API (New)" enabled.
Each search page is one billable Text Search request (up to ~21 for a full run).
"""
from dataclasses import dataclass, field
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

import environ

from apps.venues import google
from apps.venues.models import EventType, Venue

User = get_user_model()
CITY = "Addis Ababa"
IMPORT_OWNER_EMAIL = "owner@demo.yetyideges.test"


@dataclass(frozen=True)
class Profile:
    """What a search query tells us about the venues it finds."""
    query: str
    event_types: tuple[str, ...]
    capacity: tuple[int, int]
    price: int  # ETB per event day, placeholder


QUERIES = [
    Profile("wedding hall in Addis Ababa", ("wedding", "holiday-party"), (100, 600), 90000),
    Profile("event venue in Addis Ababa", ("wedding", "birthday", "holiday-party"), (50, 400), 60000),
    Profile("banquet hall in Addis Ababa", ("wedding", "graduation", "holiday-party"), (100, 500), 75000),
    Profile("hotel ballroom in Addis Ababa", ("wedding", "conference", "holiday-party"), (100, 800), 150000),
    Profile("conference hall in Addis Ababa", ("conference", "corporate-meeting"), (30, 400), 45000),
    Profile("meeting room rental in Addis Ababa", ("corporate-meeting",), (5, 60), 12000),
    Profile("garden event venue in Addis Ababa", ("wedding", "birthday", "graduation", "baby-shower"), (30, 350), 55000),
]

# Sub-cities first, then well-known neighbourhoods; first match in the address wins.
AREAS = [
    "Bole", "Kirkos", "Yeka", "Arada", "Lideta", "Gullele", "Kolfe Keranio", "Nifas Silk-Lafto",
    "Akaky Kaliti", "Addis Ketema", "Lemi Kura",
    "Kazanchis", "Piassa", "Piazza", "Sarbet", "Megenagna", "CMC", "Ayat", "Summit", "Old Airport",
    "Mexico", "Lebu", "Gerji", "Haya Hulet", "Meskel Square", "Sar Bet", "Entoto", "Saris", "Jemo",
]


def guess_area(address: str) -> str:
    low = address.lower()
    for area in AREAS:
        if area.lower() in low:
            return "Piassa" if area == "Piazza" else area
    return ""


@dataclass
class Candidate:
    place: google.PlaceResult
    profiles: list[Profile] = field(default_factory=list)

    @property
    def event_types(self):
        return sorted({t for p in self.profiles for t in p.event_types})

    @property
    def capacity(self):
        # Use the largest range among the queries that found this place.
        return max((p.capacity for p in self.profiles), key=lambda c: c[1])

    @property
    def price(self):
        return max(p.price for p in self.profiles)


class Command(BaseCommand):
    help = "Import Addis Ababa event venues from the Google Places API (demo data)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="List results without saving")
        parser.add_argument("--limit", type=int, default=60, help="Max venues to import (default 60)")
        parser.add_argument("--pages", type=int, default=2, help="Result pages per query, 20 each (max 3)")
        parser.add_argument("--refresh", action="store_true", help="Re-sync already imported venues")

    def handle(self, *args, dry_run=False, limit=60, pages=2, refresh=False, **opts):
        if not settings.GOOGLE_MAPS_API_KEY:
            raise CommandError("GOOGLE_MAPS_API_KEY is not set in .env")
        try:
            if refresh:
                return self.refresh()
            candidates = self.search(min(pages, 3))
        except google.GooglePlacesError as exc:
            raise CommandError(str(exc))

        picked = list(candidates.values())[:limit]
        self.stdout.write(f"Found {len(candidates)} unique venues in {CITY}; using {len(picked)}.")
        if dry_run:
            for c in picked:
                self.stdout.write(f"  - {c.place.name} [{guess_area(c.place.address) or '?'}] "
                                  f"{', '.join(c.event_types)}")
            return
        created, updated = self.save(picked)
        self.stdout.write(self.style.SUCCESS(f"Imported {created} new and updated {updated} venues."))

    # -------------------------------------------------------------------------
    def search(self, pages: int) -> dict[str, Candidate]:
        found: dict[str, Candidate] = {}
        for profile in QUERIES:
            n = 0
            for place in google.search_text(profile.query, max_pages=pages):
                if not place.operational or not place.name:
                    continue
                found.setdefault(place.place_id, Candidate(place)).profiles.append(profile)
                n += 1
            self.stdout.write(f"  '{profile.query}': {n} results")
        return found

    @transaction.atomic
    def save(self, candidates: list[Candidate]):
        owner = self.import_owner()
        types = {t.slug: t for t in EventType.objects.all()}
        created = updated = 0
        now = timezone.now()
        for c in candidates:
            p = c.place
            area = guess_area(p.address)
            venue = Venue.objects.filter(google_place_id=p.place_id).first()
            fields = dict(
                name=p.name[:120],
                address=p.address[:200],
                city=CITY,
                area=area,
                latitude=Decimal(str(round(p.latitude, 6))) if p.latitude is not None else None,
                longitude=Decimal(str(round(p.longitude, 6))) if p.longitude is not None else None,
                google_maps_url=p.maps_url[:500],
                google_synced_at=now,
            )
            if venue is None:
                lo, hi = c.capacity
                venue = Venue.objects.create(
                    owner=owner,
                    source=Venue.Source.GOOGLE,
                    google_place_id=p.place_id,
                    tagline=(p.type_label or "Event venue")[:160],
                    description=self.describe(p, area),
                    capacity_min=lo,
                    capacity_max=hi,
                    price_per_day=c.price,
                    details_estimated=True,
                    rental_policies="Demo listing imported from Google Maps. Contact the venue "
                                    "directly to confirm prices, capacity and policies.",
                    **fields,
                )
                created += 1
            else:
                for k, v in fields.items():
                    setattr(venue, k, v)
                venue.save()
                updated += 1
            venue.event_types.add(*[types[s] for s in c.event_types if s in types])
        return created, updated

    def refresh(self):
        venues = Venue.objects.filter(google_place_id__isnull=False)
        n = closed = 0
        for venue in venues:
            p = google.place_details(venue.google_place_id)
            venue.name, venue.address = p.name[:120] or venue.name, p.address[:200]
            if p.latitude is not None:
                venue.latitude = Decimal(str(round(p.latitude, 6)))
                venue.longitude = Decimal(str(round(p.longitude, 6)))
            venue.google_maps_url = p.maps_url[:500]
            venue.google_synced_at = timezone.now()
            if not p.operational:
                venue.is_published = False
                closed += 1
            venue.save()
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Refreshed {n} venues ({closed} closed and unpublished)."))

    @staticmethod
    def describe(p: google.PlaceResult, area: str) -> str:
        where = f"{area}, {CITY}" if area else CITY
        intro = p.summary or f"{p.type_label or 'Event venue'} in {where}."
        return (f"{intro}\n\nThis is a demo listing imported from Google Maps. The name, address and "
                f"location come from Google; price and capacity are estimates.")

    def import_owner(self):
        owner = User.objects.filter(email=IMPORT_OWNER_EMAIL).first()
        if owner:
            return owner
        env = environ.Env()
        environ.Env.read_env(settings.REPO_ROOT / ".env")
        password = env("DEMO_PASSWORD", default=None)
        if not password:
            raise CommandError("Run `manage.py seed_demo` first (or set DEMO_PASSWORD in .env).")
        return User.objects.create_user(IMPORT_OWNER_EMAIL, password, first_name="Selam",
                                        last_name="Tesfaye", role=User.Role.OWNER)
