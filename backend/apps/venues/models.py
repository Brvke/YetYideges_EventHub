from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils.text import slugify

from .images import to_webp


class EventType(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "amenities"

    def __str__(self):
        return self.name


class Venue(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="venues"
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    tagline = models.CharField(max_length=160, blank=True)
    description = models.TextField()
    city = models.CharField(max_length=80, db_index=True)
    area = models.CharField(max_length=120, blank=True, help_text="Neighbourhood / sub-city")
    address = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    capacity_min = models.PositiveIntegerField(default=1)
    capacity_max = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_per_day = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Price in ETB for one event day"
    )
    event_types = models.ManyToManyField(EventType, related_name="venues", blank=True)
    amenities = models.ManyToManyField(Amenity, related_name="venues", blank=True)
    rental_policies = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)

    # --- Imported listings (see apps/venues/google.py) ---------------------
    class Source(models.TextChoices):
        OWNER = "owner", "Added by owner"
        GOOGLE = "google", "Imported from Google Places"
        GEBETA = "gebeta", "Imported from Gebeta Maps"
        OSM = "osm", "Imported from OpenStreetMap"

    source = models.CharField(max_length=10, choices=Source.choices, default=Source.OWNER)
    gebeta_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    osm_id = models.CharField(max_length=40, unique=True, null=True, blank=True, help_text="e.g. node/123")
    # Google allows storing place IDs indefinitely; photos are never stored and
    # other fields are refreshed by `import_google_places --refresh`.
    google_place_id = models.CharField(max_length=300, unique=True, null=True, blank=True)
    google_synced_at = models.DateTimeField(null=True, blank=True)
    google_maps_url = models.URLField(max_length=500, blank=True)
    # True when price/capacity are placeholders rather than owner-provided.
    details_estimated = models.BooleanField(default=False)

    # Kept in sync by apps.reviews.signals so list pages don't aggregate per row.
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(capacity_max__gte=F("capacity_min")),
                name="venue_capacity_range_valid",
            ),
        ]
        indexes = [
            GinIndex(
                SearchVector("name", "tagline", "description", "city", "area", config="english"),
                name="venue_search_gin",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.name)[:120] or "venue"
        slug, n = base, 2
        while Venue.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug, n = f"{base}-{n}", n + 1
        return slug

    @property
    def cover_photo(self):
        return self.photos.first()


def venue_photo_path(instance, filename):
    return f"venues/{instance.venue_id}/{filename}"


class VenuePhoto(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to=venue_photo_path)
    caption = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    # For freely licensed stock photos (e.g. Wikimedia Commons): who to credit.
    credit = models.CharField(max_length=300, blank=True, help_text="Author · licence")
    credit_url = models.URLField(max_length=500, blank=True)
    is_illustrative = models.BooleanField(
        default=False, help_text="Generic photo, not of this actual venue"
    )
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        # Only re-encode freshly uploaded files, not on every save.
        if self.image and not getattr(self.image, "_committed", True):
            self.image, self.width, self.height = to_webp(
                self.image, settings.VENUE_PHOTO_MAX_EDGE
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage, name = self.image.storage, self.image.name
        super().delete(*args, **kwargs)
        if name:
            storage.delete(name)


class BlockedDate(models.Model):
    """A day the owner has marked unavailable (maintenance, private use...)."""

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="blocked_dates")
    date = models.DateField()
    reason = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(fields=["venue", "date"], name="unique_blocked_date"),
        ]

    def __str__(self):
        return f"{self.venue} – {self.date}"
