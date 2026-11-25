import django_filters
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Exists, OuterRef

from .models import BlockedDate, Venue

SEARCH_VECTOR = SearchVector("name", "tagline", "description", "city", "area", config="english")


class VenueFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_search", label="Search text")
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    event_type = django_filters.CharFilter(field_name="event_types__slug")
    guests = django_filters.NumberFilter(method="filter_guests", label="Number of guests")
    min_price = django_filters.NumberFilter(field_name="price_per_day", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price_per_day", lookup_expr="lte")
    amenities = django_filters.CharFilter(method="filter_amenities", label="Comma-separated slugs")
    available_on = django_filters.DateFilter(method="filter_available_on")
    min_rating = django_filters.NumberFilter(field_name="rating_avg", lookup_expr="gte")

    class Meta:
        model = Venue
        fields = []

    def filter_search(self, qs, name, value):
        # Full-text search (stemmed, so "weddings" matches "wedding"), with a
        # substring fallback so partial words like "ento" still find "Entoto".
        query = SearchQuery(value, config="english", search_type="websearch")
        fts = qs.annotate(rank=SearchRank(SEARCH_VECTOR, query)).filter(rank__gt=0)
        if fts.exists():
            return fts.order_by("-rank")
        return qs.filter(name__icontains=value) | qs.filter(area__icontains=value) | qs.filter(
            city__icontains=value
        )

    def filter_guests(self, qs, name, value):
        return qs.filter(capacity_min__lte=value, capacity_max__gte=value)

    def filter_amenities(self, qs, name, value):
        for slug in [s.strip() for s in value.split(",") if s.strip()]:
            qs = qs.filter(amenities__slug=slug)
        return qs

    def filter_available_on(self, qs, name, value):
        from apps.bookings.models import Booking

        booked = Booking.objects.filter(
            venue=OuterRef("pk"), event_date=value, status=Booking.Status.ACCEPTED
        )
        blocked = BlockedDate.objects.filter(venue=OuterRef("pk"), date=value)
        return qs.exclude(Exists(booked)).exclude(Exists(blocked))

    @property
    def qs(self):
        return super().qs.distinct()
