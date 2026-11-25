"""Give venues without photos free-licensed photos from Wikimedia Commons.

    python manage.py add_commons_photos --dry-run
    python manage.py add_commons_photos --max-downloads 30

For each venue that has no photos:
1. Look for a photo of that actual place ("<name> Addis Ababa"). If the file
   title clearly matches the venue name, attach it as a real photo.
2. Otherwise attach an *illustrative* photo matching the venue type (wedding
   hall, conference room, hotel ballroom, garden); the UI labels it.

Only CC0 / public domain / CC BY / CC BY-SA files are used, and the author and
licence are stored with each photo and shown in the app.
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from itertools import cycle

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.html import strip_tags

from apps.venues.models import Venue, VenuePhoto

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "YetYidegesEventHub/1.0 (demo venue photos; local development)"
OK_LICENCE = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+)", re.IGNORECASE)

# Generic interiors only: illustrative photos must not show a specific real
# place or person, so queries avoid place names and results are filtered below.
ILLUSTRATIVE = {
    "wedding": ["wedding reception hall", "wedding banquet hall", "wedding reception decoration"],
    "conference": ["conference room interior", "conference hall interior", "meeting room interior"],
    "hotel": ["hotel ballroom", "hotel banquet hall", "ballroom interior"],
    "garden": ["garden wedding reception", "outdoor wedding reception tent", "garden party tables"],
    "party": ["banquet hall tables", "banquet hall interior", "reception hall interior"],
}
GENERIC_WORDS = re.compile(
    r"banquet|ballroom|reception|wedding|conference|meeting room|auditorium|function room|event hall|party",
    re.IGNORECASE,
)
# Titles naming a city/country, a person-centred event or a document are not generic.
NOT_GENERIC = re.compile(
    r"addis|abeba|ababa|ethiopia|summit|president|minister|portrait|notepaper|letter|page|p\.\d|"
    r"street|view from|map|logo|poster|nobel|bust|statue|painting|pocahontas|shelter|taken from life|\(cropped\)",
    re.IGNORECASE,
)
OLD_PHOTO = re.compile(r"(?<!\d)(1[0-8]\d\d|19[0-8]\d)(?!\d)")
STOP = {"hotel", "the", "addis", "ababa", "international", "and", "hall", "center", "centre", "of"}


def _open(url: str, timeout: int = 60) -> bytes:
    """GET with polite pacing and back-off on 429 (Wikimedia rate limits)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        time.sleep(1.5)  # stay well under anonymous rate limits
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 4:
                wait = int(exc.headers.get("Retry-After") or 0) or 20 * (attempt + 1)
                time.sleep(min(wait, 120))
                continue
            raise CommandError(f"Wikimedia Commons error: {exc}")
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 4:
                raise CommandError(f"Wikimedia Commons unreachable: {exc}")
            time.sleep(5)


def _get(params: dict) -> dict:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})}"
    return json.loads(_open(url))


def search_files(query: str, limit: int = 12) -> list[dict]:
    """Return usable images: {title, url, page, author, licence, licence_url}."""
    data = _get({
        "action": "query", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": limit, "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime|size", "iiurlwidth": 1600,
    })
    out = []
    for page in (data.get("query") or {}).get("pages", []):
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        licence = (meta.get("LicenseShortName") or {}).get("value", "")
        if info.get("mime") not in ("image/jpeg", "image/png") or info.get("width", 0) < 1000:
            continue
        if not OK_LICENCE.match(licence) or "NC" in licence or "ND" in licence:
            continue
        if OLD_PHOTO.search(page["title"]):  # skip historical photos (e.g. "1909")
            continue
        author = strip_tags((meta.get("Artist") or {}).get("value", "")).strip() or "Unknown author"
        out.append({
            "title": page["title"],
            "url": info.get("thumburl") or info["url"],
            "page": info.get("descriptionurl", ""),
            "author": re.sub(r"\s+", " ", author)[:120],
            "licence": licence,
        })
    return out


def is_generic(title: str, venue_names: list[str]) -> bool:
    """A stock photo is usable as 'illustrative' only if it's clearly generic."""
    if not GENERIC_WORDS.search(title) or NOT_GENERIC.search(title):
        return False
    return not any(matches_any(title, n) for n in venue_names)


def matches_any(title: str, venue_name: str) -> bool:
    tokens = name_tokens(venue_name)
    return bool(tokens) and all(tok in title.lower() for tok in tokens)


def name_tokens(name: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", name.lower()) if w not in STOP}


def matches_venue(title: str, venue_name: str) -> bool:
    tokens = name_tokens(venue_name)
    t = title.lower()
    return bool(tokens) and all(tok in t for tok in tokens) and "addis" in t


def kind_of(venue: Venue) -> str:
    slugs = set(venue.event_types.values_list("slug", flat=True))
    text = f"{venue.name} {venue.tagline}".lower()
    if "garden" in text:
        return "garden"
    if "hotel" in text:
        return "hotel"
    if slugs & {"conference", "corporate-meeting"} and not slugs & {"wedding"}:
        return "conference"
    if "wedding" in slugs:
        return "wedding"
    return "party"


class Command(BaseCommand):
    help = "Attach free-licensed Wikimedia Commons photos to venues that have none."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--max-downloads", type=int, default=30)
        parser.add_argument("--redo-illustrative", action="store_true",
                            help="Delete existing illustrative photos first and pick again")

    def handle(self, *args, dry_run=False, max_downloads=30, redo_illustrative=False, **opts):
        if redo_illustrative and not dry_run:
            old = list(VenuePhoto.objects.filter(is_illustrative=True))
            for photo in old:
                photo.delete()  # also removes the file
            self.stdout.write(f"Removed {len(old)} illustrative photos.")
        venues = list(Venue.objects.filter(photos__isnull=True).order_by("id"))
        self.stdout.write(f"{len(venues)} venues have no photos.")
        pools: dict[str, cycle] = {}
        used: set[str] = set()
        downloads = real = 0

        for venue in venues:
            if downloads >= max_downloads:
                self.stdout.write("Reached --max-downloads; stopping.")
                break
            photo, illustrative = None, True
            if venue.source != Venue.Source.OWNER or venue.osm_id:
                for f in search_files(f"{venue.name} Addis Ababa", limit=8):
                    if f["url"] not in used and matches_venue(f["title"], venue.name):
                        photo, illustrative = f, False
                        break
            if photo is None:
                kind = kind_of(venue)
                if kind not in pools:
                    venue_names = [n for n in Venue.objects.values_list("name", flat=True)]
                    found = [
                        f for q in ILLUSTRATIVE[kind] for f in search_files(q)
                        if is_generic(f["title"], venue_names)
                    ]
                    self.stdout.write(f"  ({len(found)} generic '{kind}' photos available)")
                    pools[kind] = cycle(found) if found else None
                pool = pools[kind]
                if pool is None:
                    continue
                for _ in range(40):
                    f = next(pool)
                    if f["url"] not in used:
                        photo = f
                        break
                else:
                    photo = next(pool)  # pool exhausted: reuse
            used.add(photo["url"])
            label = "real" if not illustrative else "illustrative"
            self.stdout.write(f"  {venue.name}: {label} - {photo['title'][5:70]} ({photo['licence']})")
            if dry_run:
                continue
            self.attach(venue, photo, illustrative)
            downloads += 1
            real += not illustrative

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"Added {downloads} photos ({real} of the actual venue, {downloads - real} illustrative)."))

    def attach(self, venue, photo, illustrative):
        content = _open(photo["url"], timeout=120)
        name = re.sub(r"[^A-Za-z0-9_.-]+", "_", photo["title"].split(":", 1)[-1])[:80]
        VenuePhoto.objects.create(
            venue=venue,
            image=ContentFile(content, name=name),
            caption="" if illustrative else venue.name,
            credit=f"{photo['author']} · {photo['licence']} · Wikimedia Commons"[:300],
            credit_url=photo["page"][:500],
            is_illustrative=illustrative,
            order=0,
        )
