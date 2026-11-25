"""Import Addis Ababa hotels and event venues from OpenStreetMap (free, no key).

    python manage.py import_osm_venues --dry-run
    python manage.py import_osm_venues --limit 30

Uses the public Overpass API. OpenStreetMap data is licensed under the ODbL:
the app credits "© OpenStreetMap contributors" on imported venues.
Price and capacity aren't in the data, so they're estimates (`details_estimated`).
"""
import json
import re
import time
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.venues.models import EventType, Venue

from .import_gebeta_places import NOT_VENUE_WORDS, Command as GebetaCommand
from .import_google_places import CITY, Command as GoogleCommand, Profile, guess_area

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
USER_AGENT = "YetYidegesEventHub/1.0 (demo venue importer)"
BBOX = "8.83,38.63,9.10,38.92"  # south,west,north,east around Addis Ababa
QUERY = f"""
[out:json][timeout:90];
(
  nwr["tourism"="hotel"]["name"]({BBOX});
  nwr["amenity"~"^(events_venue|conference_centre)$"]["name"]({BBOX});
  nwr["amenity"="community_centre"]["name"~"[Hh]all|አዳራሽ"]({BBOX});
);
out tags center;
"""

PROFILES = {
    "events_venue": Profile("", ("wedding", "birthday", "graduation", "holiday-party"), (80, 500), 70000),
    "conference_centre": Profile("", ("conference", "corporate-meeting"), (30, 500), 50000),
    "community_centre": Profile("", ("wedding", "birthday", "graduation"), (50, 300), 35000),
    "hotel_big": Profile("", ("wedding", "conference", "corporate-meeting", "holiday-party"), (100, 800), 150000),
    "hotel": Profile("", ("wedding", "corporate-meeting", "birthday", "holiday-party"), (30, 250), 60000),
}


CACHE = Path(__file__).resolve().parents[4] / ".cache" / "osm_addis.json"


def fetch_overpass(stdout, use_cache=False, attempts=2) -> list[dict]:
    if use_cache and CACHE.exists():
        stdout.write(f"  using cached download {CACHE.name}")
        return json.loads(CACHE.read_text(encoding="utf-8"))["elements"]
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    last = None
    for attempt in range(attempts):
        for url in OVERPASS_SERVERS:
            req = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    raw = resp.read().decode("utf-8")
                elements = json.loads(raw)["elements"]
                CACHE.parent.mkdir(exist_ok=True)
                CACHE.write_text(raw, encoding="utf-8")
                return elements
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
                last = exc
                stdout.write(f"  {urllib.parse.urlparse(url).netloc} unavailable ({exc}); trying next...")
        time.sleep(20)
    raise CommandError(f"All Overpass servers failed: {last}")


def profile_for(tags: dict) -> Profile:
    if tags.get("tourism") == "hotel":
        try:
            stars = float(tags.get("stars", "0").split()[0])
        except ValueError:
            stars = 0
        return PROFILES["hotel_big"] if stars >= 4 else PROFILES["hotel"]
    return PROFILES[tags.get("amenity", "events_venue")]


def display_name(tags: dict) -> str:
    return (tags.get("name:en") or tags.get("name") or "").strip()


class Command(BaseCommand):
    help = "Import Addis Ababa hotels and event venues from OpenStreetMap (demo data)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=30, help="Max venues (default 30)")
        parser.add_argument("--cached", action="store_true", help="Reuse the last successful download")
        parser.add_argument("--attempts", type=int, default=2, help="Rounds of retries across servers")

    def handle(self, *args, dry_run=False, limit=30, cached=False, attempts=2, **opts):
        self.stdout.write("Querying OpenStreetMap (Overpass)...")
        elements = [
            e for e in fetch_overpass(self.stdout, use_cache=cached, attempts=attempts)
            if display_name(e.get("tags", {}))
            and not NOT_VENUE_WORDS.search(display_name(e["tags"]))
            and not re.search(r"factory|furniture|pension|guest ?house", display_name(e["tags"]), re.I)
        ]
        # Venue-type places first (they're rarer), then the best-rated hotels.
        def rank(e):
            t = e["tags"]
            if t.get("amenity") in ("events_venue", "conference_centre"):
                return (0, 0)
            if t.get("tourism") == "hotel":
                try:
                    return (1, -float(t.get("stars", "0").split()[0]))
                except ValueError:
                    return (1, 0)
            return (2, 0)

        elements.sort(key=rank)
        picked = elements[:limit]
        self.stdout.write(f"Found {len(elements)} named places; using {len(picked)}.")
        if dry_run:
            for e in picked:
                t = e["tags"]
                kind = t.get("amenity") or t.get("tourism")
                self.stdout.write(f"  - {display_name(t)}  [{kind}{', ' + t['stars'] + '*' if t.get('stars') else ''}]")
            return
        created, updated, skipped = self.save(picked)
        self.stdout.write(self.style.SUCCESS(
            f"Imported {created} new, updated {updated}, skipped {skipped} already listed."))

    @transaction.atomic
    def save(self, elements):
        owner = GoogleCommand().import_owner()
        dupes = GebetaCommand()
        types = {t.slug: t for t in EventType.objects.all()}
        created = updated = skipped = 0
        for e in elements:
            t = e["tags"]
            lat = e.get("lat") or (e.get("center") or {}).get("lat")
            lon = e.get("lon") or (e.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            osm_id = f"{e['type']}/{e['id']}"
            name = display_name(t)
            street = " ".join(filter(None, [t.get("addr:housenumber"), t.get("addr:street")]))
            area = (t.get("addr:suburb") or t.get("addr:district") or guess_area(f"{name} {street}"))[:120]
            fields = dict(
                name=name[:120], city=CITY, area=area,
                address=", ".join(filter(None, [street, area, CITY]))[:200],
                latitude=Decimal(str(round(lat, 6))), longitude=Decimal(str(round(lon, 6))),
            )
            venue = Venue.objects.filter(osm_id=osm_id).first()
            if venue:
                for k, v in fields.items():
                    setattr(venue, k, v)
                venue.save()
                updated += 1
            else:
                probe = type("P", (), {"name": name, "latitude": lat, "longitude": lon})
                if dupes.duplicate_of(probe):
                    skipped += 1
                    continue
                p = profile_for(t)
                kind = {"events_venue": "Event venue", "conference_centre": "Conference centre",
                        "community_centre": "Community hall"}.get(t.get("amenity"), "Hotel")
                stars = f"{t['stars']}-star " if t.get("stars") and kind == "Hotel" else ""
                contact = [f"Phone: {t.get('phone') or t.get('contact:phone')}" if (t.get("phone") or t.get("contact:phone")) else "",
                           f"Website: {t.get('website') or t.get('contact:website')}" if (t.get("website") or t.get("contact:website")) else ""]
                where = f"{area}, {CITY}" if area else CITY
                venue = Venue.objects.create(
                    owner=owner, source=Venue.Source.OSM, osm_id=osm_id,
                    tagline=f"{stars}{kind.lower() if stars else kind} in {where}"[:160],
                    description="\n".join(filter(None, [
                        f"{name} is a {stars}{kind.lower()} in {where}.",
                        *contact,
                        "",
                        "Demo listing: name and location from OpenStreetMap (© OpenStreetMap contributors, ODbL). "
                        "Price and capacity are estimates. Photos labelled illustrative are not of this venue.",
                    ])),
                    capacity_min=p.capacity[0], capacity_max=p.capacity[1], price_per_day=p.price,
                    details_estimated=True,
                    rental_policies="Demo listing. Contact the venue directly to confirm prices, capacity and policies.",
                    **fields,
                )
                venue.event_types.add(*[types[s] for s in p.event_types if s in types])
                created += 1
        return created, updated, skipped
