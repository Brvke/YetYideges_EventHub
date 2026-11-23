from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.bookings.models import Booking
from apps.venues.models import Venue


class Review(models.Model):
    """One review per accepted booking, written after the event day."""

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    owner_reply = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5), name="review_rating_1_to_5"
            ),
        ]

    def __str__(self):
        return f"{self.rating}★ {self.venue} by {self.author}"
