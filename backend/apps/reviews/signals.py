from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review


@receiver([post_save, post_delete], sender=Review)
def refresh_venue_rating(sender, instance, **kwargs):
    venue = instance.venue
    agg = venue.reviews.aggregate(avg=Avg("rating"), n=Count("id"))
    venue.rating_avg = round(agg["avg"] or 0, 2)
    venue.rating_count = agg["n"]
    venue.save(update_fields=["rating_avg", "rating_count"])
