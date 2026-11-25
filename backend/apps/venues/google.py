"""Minimal client for the Google Places API (New).

Docs: https://developers.google.com/maps/documentation/places/web-service/op-overview

How we follow Google's terms:
- Only the place ID is kept long-term. Name/address/location are refreshed
  with `manage.py import_google_places --refresh`.
- Photos are never downloaded or stored. Each request asks Google for a
  short-lived photo URL and the photographer attribution, which the frontend
  shows next to the photo along with "Google Maps". Results are held in the
  process cache for a few minutes only, to avoid duplicate calls while a page
  loads.

The API key comes from GOOGLE_MAPS_API_KEY in the repo's .env file.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

BASE = "https://places.googleapis.com/v1"
SHORT_CACHE_SECONDS = 300
TIMEOUT = 15

# Rough bounding box of Addis Ababa city administration.
ADDIS_ABABA_BOUNDS = {
    "low": {"latitude": 8.83, "longitude": 38.63},
    "high": {"latitude": 9.10, "longitude": 38.92},
}


class GooglePlacesError(Exception):
    pass


class GooglePlacesNotConfigured(GooglePlacesError):
    pass


def _key() -> str:
    key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
    if not key:
        raise GooglePlacesNotConfigured("Set GOOGLE_MAPS_API_KEY in .env")
    return key


def _call(method: str, path: str, *, body: dict | None = None, field_mask: str | None = None,
          query: dict | None = None) -> dict:
    url = f"{BASE}/{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    headers = {"X-Goog-Api-Key": _key(), "Content-Type": "application/json"}
    if field_mask:
        headers["X-Goog-FieldMask"] = field_mask
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise GooglePlacesError(f"Google Places {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise GooglePlacesError(f"Could not reach Google Places: {exc.reason}") from exc


# ------------------------------------------------------------------ search --
SEARCH_FIELDS = ",".join(
    f"places.{f}" for f in [
        "id", "displayName", "formattedAddress", "location", "types",
        "primaryTypeDisplayName", "editorialSummary", "googleMapsUri", "businessStatus",
    ]
) + ",nextPageToken"


@dataclass
class PlaceResult:
    place_id: str
    name: str
    address: str
    latitude: float | None
    longitude: float | None
    types: list[str]
    type_label: str
    summary: str
    maps_url: str
    operational: bool

    @classmethod
    def from_api(cls, p: dict) -> "PlaceResult":
        loc = p.get("location") or {}
        return cls(
            place_id=p["id"],
            name=(p.get("displayName") or {}).get("text", "").strip(),
            address=p.get("formattedAddress", ""),
            latitude=loc.get("latitude"),
            longitude=loc.get("longitude"),
            types=p.get("types", []),
            type_label=(p.get("primaryTypeDisplayName") or {}).get("text", ""),
            summary=(p.get("editorialSummary") or {}).get("text", ""),
            maps_url=p.get("googleMapsUri", ""),
            operational=p.get("businessStatus", "OPERATIONAL") == "OPERATIONAL",
        )


def search_text(query: str, *, bounds: dict = ADDIS_ABABA_BOUNDS, max_pages: int = 3):
    """Yield PlaceResults for a text query restricted to `bounds` (≤20 per page)."""
    token = None
    for _ in range(max_pages):
        body = {"textQuery": query, "pageSize": 20, "locationRestriction": {"rectangle": bounds}}
        if token:
            body["pageToken"] = token
        data = _call("POST", "places:searchText", body=body, field_mask=SEARCH_FIELDS)
        for p in data.get("places", []):
            yield PlaceResult.from_api(p)
        token = data.get("nextPageToken")
        if not token:
            break


def place_details(place_id: str) -> PlaceResult:
    fields = SEARCH_FIELDS.replace("places.", "").replace(",nextPageToken", "")
    return PlaceResult.from_api(_call("GET", f"places/{place_id}", field_mask=fields))


# ------------------------------------------------------------------ photos --
def place_photos(place_id: str, limit: int = 8) -> list[dict]:
    """Fresh photo references + attributions for a place (briefly cached)."""
    ck = f"gplaces:photos:{place_id}"
    photos = cache.get(ck)
    if photos is None:
        data = _call("GET", f"places/{place_id}", field_mask="photos")
        photos = [
            {
                "name": ph["name"],
                "width": ph.get("widthPx", 0),
                "height": ph.get("heightPx", 0),
                "attributions": [
                    {"name": a.get("displayName", ""), "url": a.get("uri", "")}
                    for a in ph.get("authorAttributions", [])
                ],
            }
            for ph in data.get("photos", [])[:limit]
        ]
        cache.set(ck, photos, SHORT_CACHE_SECONDS)
    return photos


def photo_url(photo_name: str, max_px: int = 1200) -> str:
    """Short-lived googleusercontent URL for a photo reference (briefly cached)."""
    ck = f"gplaces:uri:{photo_name}:{max_px}"
    uri = cache.get(ck)
    if uri is None:
        data = _call("GET", f"{photo_name}/media",
                     query={"maxWidthPx": max_px, "skipHttpRedirect": "true"})
        uri = data.get("photoUri", "")
        cache.set(ck, uri, SHORT_CACHE_SECONDS)
    return uri
