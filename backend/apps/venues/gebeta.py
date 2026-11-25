"""Minimal client for Gebeta Maps forward geocoding (Ethiopian map data).

Docs: https://docs.gebeta.app/docs/geocoding/geocoding-forward

    GET https://mapapi.gebeta.app/v2/search/geocode?query=...&apiKey=...
        optional: bbox=minLng,minLat,maxLng,maxLat  country=et  limit=1..10
                  autocomplete=false  proximity=lng,lat  category=...

Each call returns at most 10 results, so the importer splits Addis Ababa into a
grid of smaller boxes and searches each one. The free Developer plan includes
1,500 geocoding calls. Results carry name, location, category, city and
neighbourhood only: no photos or phone numbers.

The key comes from GEBETA_API_KEY in the repo's .env file. Gebeta only accepts
it as a query parameter, so never log full request URLs.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.conf import settings

URL = "https://mapapi.gebeta.app/v2/search/geocode"
TIMEOUT = 20

# (min_lng, min_lat, max_lng, max_lat) around Addis Ababa city administration
ADDIS_ABABA_BBOX = (38.63, 8.83, 38.92, 9.10)


class GebetaError(Exception):
    pass


class GebetaNotConfigured(GebetaError):
    pass


@dataclass
class GebetaPlace:
    id: str
    name: str
    display_name: str
    category: str
    latitude: float | None
    longitude: float | None
    city: str
    neighborhood: str

    @classmethod
    def from_api(cls, r: dict) -> "GebetaPlace":
        loc = r.get("location") or {}
        addr = r.get("address") or {}
        return cls(
            id=str(r.get("id", "")),
            name=(r.get("name") or "").strip(),
            display_name=r.get("display_name", ""),
            category=r.get("category") or "",
            latitude=loc.get("lat"),
            longitude=loc.get("lng"),
            city=addr.get("city", ""),
            neighborhood=r.get("neighborhood") or "",
        )


def grid(bbox=ADDIS_ABABA_BBOX, n: int = 3):
    """Split a bbox into n×n smaller boxes (each search returns ≤10 results)."""
    min_lng, min_lat, max_lng, max_lat = bbox
    dx, dy = (max_lng - min_lng) / n, (max_lat - min_lat) / n
    for i in range(n):
        for j in range(n):
            yield (round(min_lng + i * dx, 5), round(min_lat + j * dy, 5),
                   round(min_lng + (i + 1) * dx, 5), round(min_lat + (j + 1) * dy, 5))


def search(query: str, bbox=ADDIS_ABABA_BBOX, limit: int = 10) -> list[GebetaPlace]:
    key = getattr(settings, "GEBETA_API_KEY", "")
    if not key:
        raise GebetaNotConfigured("Set GEBETA_API_KEY in .env")
    params = {
        "query": query,
        "apiKey": key,
        "country": "et",
        "limit": max(1, min(limit, 10)),
        "autocomplete": "false",
        "bbox": ",".join(str(v) for v in bbox),
    }
    req = urllib.request.Request(f"{URL}?{urllib.parse.urlencode(params)}",
                                 headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:300]
        if exc.code == 401:
            raise GebetaError("Gebeta rejected the API key (401). Check GEBETA_API_KEY in .env.") from exc
        raise GebetaError(f"Gebeta {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise GebetaError(f"Could not reach Gebeta Maps: {exc.reason}") from exc
    results = (data.get("data") or {}).get("results") or []
    return [GebetaPlace.from_api(r) for r in results]
