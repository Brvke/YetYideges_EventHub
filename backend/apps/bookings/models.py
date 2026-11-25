from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from apps.venues.models import EventType, Venue


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    ACTIVE = (Status.PENDING, Status.ACCEPTED)

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="bookings")
    guest = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    event_date = models.DateField()
    guest_count = models.PositiveIntegerField()
    event_type = models.ForeignKey(EventType, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    owner_note = models.CharField(max_length=300, blank=True)
    # Price is copied at request time so later price changes don't alter it.
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # The core rule: a venue can never be double-booked for a day.
            models.UniqueConstraint(
                fields=["venue", "event_date"],
                condition=Q(status="accepted"),
                name="one_accepted_booking_per_venue_day",
            ),
            # A guest can't spam several open requests for the same day.
            models.UniqueConstraint(
                fields=["venue", "guest", "event_date"],
                condition=Q(status__in=["pending", "accepted"]),
                name="one_open_request_per_guest_day",
            ),
        ]
        indexes = [models.Index(fields=["venue", "event_date", "status"])]

    def __str__(self):
        return f"{self.venue} · {self.event_date} · {self.guest} ({self.status})"

    # ---- derived state -------------------------------------------------
    @property
    def is_past(self):
        return self.event_date < timezone.localdate()

    @property
    def can_review(self):
        return (
            self.status == self.Status.ACCEPTED
            and self.event_date <= timezone.localdate()
            and not hasattr(self, "review")
        )

    # ---- validation ----------------------------------------------------
    def clean(self):
        errors = {}
        venue = self.venue
        if self.event_date and self.event_date <= timezone.localdate():
            errors["event_date"] = "Choose a future date."
        if self.guest_count and venue and not (
            venue.capacity_min <= self.guest_count <= venue.capacity_max
        ):
            errors["guest_count"] = (
                f"This venue hosts {venue.capacity_min}–{venue.capacity_max} guests."
            )
        if venue and self.event_date:
            if venue.blocked_dates.filter(date=self.event_date).exists():
                errors["event_date"] = "The venue is not available on this date."
            elif (
                venue.bookings.filter(event_date=self.event_date, status=self.Status.ACCEPTED)
                .exclude(pk=self.pk)
                .exists()
            ):
                errors["event_date"] = "This date is already booked."
        if errors:
            raise ValidationError(errors)

    # ---- transitions ---------------------------------------------------
    def _transition(self, allowed_from, to, note=""):
        if self.status not in allowed_from:
            raise ValidationError(f"Cannot change a {self.status} booking to {to}.")
        self.status = to
        self.owner_note = note or self.owner_note
        self.responded_at = timezone.now()

    @transaction.atomic
    def accept(self, note=""):
        # Lock competing requests for this venue/day so two owners' clicks
        # (or two tabs) can't both win; the DB constraint is the final guard.
        competing = (
            Booking.objects.select_for_update()
            .filter(venue=self.venue, event_date=self.event_date, status=self.Status.PENDING)
            .exclude(pk=self.pk)
        )
        if self.is_past:
            raise ValidationError("This date has already passed.")
        self._transition([self.Status.PENDING], self.Status.ACCEPTED, note)
        self.save()
        competing.update(
            status=self.Status.DECLINED,
            owner_note="Another booking was confirmed for this date.",
            responded_at=timezone.now(),
        )

    def decline(self, note=""):
        self._transition([self.Status.PENDING], self.Status.DECLINED, note)
        self.save()

    def cancel(self):
        if self.is_past:
            raise ValidationError("Past bookings can't be cancelled.")
        self._transition(list(self.ACTIVE), self.Status.CANCELLED)
        self.save()
