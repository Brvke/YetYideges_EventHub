from datetime import date, timedelta

from django.db.models import Count, Prefetch, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsVenueOwner

from .filters import VenueFilter
from .models import Amenity, BlockedDate, EventType, Venue, VenuePhoto
from .serializers import (
    AmenitySerializer,
    BlockedDateSerializer,
    EventTypeSerializer,
    PhotoUploadSerializer,
    VenueDetailSerializer,
    VenueListSerializer,
    VenuePhotoSerializer,
    VenueWriteSerializer,
)

MAX_AVAILABILITY_RANGE_DAYS = 400


def venue_queryset():
    return Venue.objects.select_related("owner").prefetch_related(
        "event_types", "amenities", Prefetch("photos", queryset=VenuePhoto.objects.order_by("order", "id"))
    )


# ---------------------------------------------------------------- public ----
class VenueViewSet(viewsets.ReadOnlyModelViewSet):
    """Published venues: browse, search, view details and availability."""

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    filterset_class = VenueFilter
    ordering_fields = ["price_per_day", "rating_avg", "capacity_max", "created_at"]

    def get_queryset(self):
        return venue_queryset().filter(is_published=True)

    def get_serializer_class(self):
        return VenueDetailSerializer if self.action == "retrieve" else VenueListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("start", str, description="YYYY-MM-DD, default today"),
            OpenApiParameter("end", str, description="YYYY-MM-DD, default start + 90 days"),
        ]
    )
    @action(detail=True)
    def availability(self, request, slug=None):
        """Dates that are booked or blocked between `start` and `end`."""
        venue = self.get_object()
        try:
            start = date.fromisoformat(request.query_params.get("start", ""))
        except ValueError:
            start = date.today()
        try:
            end = date.fromisoformat(request.query_params.get("end", ""))
        except ValueError:
            end = start + timedelta(days=90)
        if end < start or (end - start).days > MAX_AVAILABILITY_RANGE_DAYS:
            return Response(
                {"detail": f"Range must be 0–{MAX_AVAILABILITY_RANGE_DAYS} days."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booked = venue.bookings.filter(
            status="accepted", event_date__range=(start, end)
        ).values_list("event_date", flat=True)
        blocked = venue.blocked_dates.filter(date__range=(start, end)).values_list("date", flat=True)
        return Response(
            {
                "start": start,
                "end": end,
                "unavailable": sorted(set(booked) | set(blocked)),
            }
        )


class EventTypeList(generics.ListAPIView):
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class AmenityList(generics.ListAPIView):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class CityList(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        rows = (
            Venue.objects.filter(is_published=True)
            .values("city")
            .annotate(venue_count=Count("id"))
            .order_by("-venue_count", "city")
        )
        return Response(list(rows))


# ----------------------------------------------------------------- owner ----
class OwnerVenueViewSet(viewsets.ModelViewSet):
    """The signed-in owner's own venues (published or not)."""

    permission_classes = [IsVenueOwner]
    serializer_class = VenueWriteSerializer

    def get_queryset(self):
        return venue_queryset().filter(owner=self.request.user).annotate(
            pending_requests=Count("bookings", filter=Q(bookings__status="pending"))
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OwnerPhotoViewSet(
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """Upload (several at once), reorder/caption and delete venue photos."""

    permission_classes = [IsVenueOwner]
    serializer_class = VenuePhotoSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return VenuePhoto.objects.filter(venue__owner=self.request.user)

    @extend_schema(request=PhotoUploadSerializer, responses=VenuePhotoSerializer(many=True))
    def create(self, request):
        upload = PhotoUploadSerializer(data=request.data, context={"request": request})
        upload.is_valid(raise_exception=True)
        venue = upload.validated_data["venue"]
        start = venue.photos.count()
        photos = [
            VenuePhoto.objects.create(venue=venue, image=img, order=start + i)
            for i, img in enumerate(upload.validated_data["images"])
        ]
        data = VenuePhotoSerializer(photos, many=True, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class OwnerBlockedDateViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsVenueOwner]
    serializer_class = BlockedDateSerializer
    filterset_fields = ["venue"]
    pagination_class = None

    def get_queryset(self):
        return BlockedDate.objects.filter(venue__owner=self.request.user)
