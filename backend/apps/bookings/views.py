from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsVenueOwner
from apps.venues.models import Venue

from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer, OwnerDecisionSerializer


def _error(exc):
    msg = exc.messages[0] if isinstance(exc, DjangoValidationError) else str(exc)
    return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)


def booking_queryset():
    return Booking.objects.select_related("venue", "guest", "event_type", "review").prefetch_related(
        "venue__photos"
    )


class GuestBookingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Bookings the signed-in user has requested."""

    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status"]

    def get_queryset(self):
        qs = booking_queryset().filter(guest=self.request.user)
        when = self.request.query_params.get("when")
        today = timezone.localdate()
        if when == "upcoming":
            qs = qs.filter(event_date__gte=today).order_by("event_date")
        elif when == "past":
            qs = qs.filter(event_date__lt=today).order_by("-event_date")
        return qs

    def get_serializer_class(self):
        return BookingCreateSerializer if self.action == "create" else BookingSerializer

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        try:
            booking.cancel()
        except DjangoValidationError as exc:
            return _error(exc)
        return Response(BookingSerializer(booking, context={"request": request}).data)


class OwnerBookingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Booking requests for the signed-in owner's venues."""

    permission_classes = [IsVenueOwner]
    serializer_class = BookingSerializer
    filterset_fields = ["status", "venue"]
    ordering_fields = ["event_date", "created_at"]

    def get_queryset(self):
        return booking_queryset().filter(venue__owner=self.request.user)

    def _decide(self, request, verb):
        booking = self.get_object()
        decision = OwnerDecisionSerializer(data=request.data)
        decision.is_valid(raise_exception=True)
        try:
            getattr(booking, verb)(decision.validated_data.get("note", ""))
        except DjangoValidationError as exc:
            return _error(exc)
        except IntegrityError:
            return Response(
                {"detail": "Another booking was already confirmed for this date."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(BookingSerializer(booking, context={"request": request}).data)

    @extend_schema(request=OwnerDecisionSerializer)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._decide(request, "accept")

    @extend_schema(request=OwnerDecisionSerializer)
    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        return self._decide(request, "decline")


class OwnerStatsView(APIView):
    """Headline numbers for the owner dashboard."""

    permission_classes = [IsVenueOwner]

    def get(self, request):
        today = timezone.localdate()
        bookings = Booking.objects.filter(venue__owner=request.user)
        venues = Venue.objects.filter(owner=request.user)
        accepted = bookings.filter(status=Booking.Status.ACCEPTED)
        rated = venues.filter(rating_count__gt=0)
        return Response(
            {
                "venues": venues.count(),
                "published_venues": venues.filter(is_published=True).count(),
                "pending_requests": bookings.filter(
                    status=Booking.Status.PENDING, event_date__gte=today
                ).count(),
                "upcoming_events": accepted.filter(event_date__gte=today).count(),
                "revenue_this_year": accepted.filter(event_date__year=today.year).aggregate(
                    s=Sum("quoted_price")
                )["s"]
                or 0,
                "average_rating": round(rated.aggregate(a=Avg("rating_avg"))["a"] or 0, 2),
                "review_count": rated.aggregate(n=Sum("rating_count"))["n"] or 0,
                "acceptance_rate": _acceptance_rate(bookings),
            }
        )


def _acceptance_rate(bookings):
    agg = bookings.aggregate(
        decided=Count("id", filter=Q(status__in=["accepted", "declined"])),
        accepted=Count("id", filter=Q(status="accepted")),
    )
    return round(agg["accepted"] / agg["decided"] * 100) if agg["decided"] else None
