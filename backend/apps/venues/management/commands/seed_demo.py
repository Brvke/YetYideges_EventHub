"""Fill the database with demo data for local development.

    python manage.py seed_demo           # idempotent: safe to run again
    python manage.py seed_demo --reset   # wipe venues/bookings/reviews first

Demo accounts use the DEMO_PASSWORD value from the repo's .env file:
    owner@demo.yetyideges.test   (venue owner)
    guest@demo.yetyideges.test   (guest)
"""
from datetime import timedelta
from decimal import Decimal

import environ
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.bookings.models import Booking
from apps.reviews.models import Review
from apps.venues.models import Amenity, EventType, Venue

User = get_user_model()

EVENT_TYPES = ["Wedding", "Birthday", "Corporate meeting", "Conference", "Concert", "Graduation", "Baby shower", "Holiday party"]
AMENITIES = ["Parking", "Wi-Fi", "Catering", "Sound system", "Projector", "Garden", "Air conditioning",
             "Stage", "Dance floor", "Wheelchair access", "Generator backup", "Decoration service"]

VENUES = [
    dict(name="Entoto Hills Garden", city="Addis Ababa", area="Entoto", lat="9.0849", lng="38.7626",
         cap=(50, 600), price=85000, types=["Wedding", "Graduation", "Holiday party"],
         amen=["Parking", "Garden", "Catering", "Generator backup", "Dance floor", "Decoration service"],
         tagline="Open-air celebrations with a view over the whole city",
         desc="A eucalyptus-ringed garden on the slopes of Entoto with panoramic views of Addis Ababa. "
              "Ideal for large weddings and outdoor receptions, with a covered pavilion for the rainy season."),
    dict(name="Bole Skyline Hall", city="Addis Ababa", area="Bole", lat="8.9956", lng="38.7869",
         cap=(80, 400), price=120000, types=["Wedding", "Conference", "Holiday party"],
         amen=["Parking", "Wi-Fi", "Air conditioning", "Sound system", "Stage", "Projector", "Wheelchair access"],
         tagline="A modern ballroom minutes from the airport",
         desc="Floor-to-ceiling windows, crystal lighting and an in-house AV team. A favourite for "
              "evening weddings and gala dinners in the heart of Bole."),
    dict(name="Kazanchis Business Centre", city="Addis Ababa", area="Kazanchis", lat="9.0147", lng="38.7631",
         cap=(10, 150), price=28000, types=["Corporate meeting", "Conference"],
         amen=["Wi-Fi", "Projector", "Air conditioning", "Catering", "Wheelchair access"],
         tagline="Meeting rooms and a 150-seat auditorium",
         desc="Flexible meeting rooms and a tiered auditorium with simultaneous translation booths, "
              "a short walk from the UNECA compound."),
    dict(name="Piassa Heritage House", city="Addis Ababa", area="Piassa", lat="9.0350", lng="38.7520",
         cap=(20, 120), price=40000, types=["Birthday", "Baby shower", "Graduation"],
         amen=["Garden", "Catering", "Decoration service", "Sound system"],
         tagline="A restored 1920s villa with a courtyard garden",
         desc="Hand-carved wooden balconies, a jasmine-scented courtyard and a traditional coffee "
              "ceremony corner. Perfect for intimate family celebrations."),
    dict(name="Sarbet Rooftop Lounge", city="Addis Ababa", area="Sarbet", lat="8.9989", lng="38.7406",
         cap=(15, 90), price=35000, types=["Birthday", "Holiday party", "Concert"],
         amen=["Sound system", "Dance floor", "Wi-Fi", "Catering"],
         tagline="Sunset parties above the city lights",
         desc="An open rooftop with a bar, DJ booth and heaters for cool evenings."),
    dict(name="Lake Babogaya Resort Pavilion", city="Bishoftu", area="Lake Babogaya", lat="8.7870", lng="38.9890",
         cap=(40, 300), price=95000, types=["Wedding", "Corporate meeting", "Conference"],
         amen=["Parking", "Garden", "Catering", "Wi-Fi", "Generator backup", "Stage"],
         tagline="Lakeside weddings an hour from Addis",
         desc="A lakeside pavilion with lawns running down to the water. Guest rooms on site for "
              "two-day celebrations and company retreats."),
    dict(name="Hawassa Lakeshore Gardens", city="Hawassa", area="Lakeshore", lat="7.0621", lng="38.4764",
         cap=(30, 500), price=60000, types=["Wedding", "Concert", "Graduation"],
         amen=["Parking", "Garden", "Stage", "Sound system", "Catering"],
         tagline="Big celebrations on the shore of Lake Hawassa",
         desc="Wide lawns shaded by fig trees along the lake, with a permanent stage for concerts."),
    dict(name="Bahir Dar Riverside Hall", city="Bahir Dar", area="Blue Nile", lat="11.5936", lng="37.3908",
         cap=(50, 350), price=55000, types=["Wedding", "Conference", "Graduation"],
         amen=["Parking", "Air conditioning", "Projector", "Sound system", "Wheelchair access"],
         tagline="Where Lake Tana meets the Blue Nile",
         desc="A bright hall with a terrace overlooking the river, popular for university graduations."),
]

REVIEWS = [
    (5, "Everything was perfect. The staff helped with decoration and the view was stunning."),
    (4, "Great venue, parking filled up quickly but the team sorted it out."),
    (5, "Our guests are still talking about it. Highly recommended."),
]


class Command(BaseCommand):
    help = "Create demo venues, accounts, bookings and reviews."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing venues first")

    @transaction.atomic
    def handle(self, *args, reset=False, **opts):
        env = environ.Env()
        environ.Env.read_env(settings.REPO_ROOT / ".env")
        password = env("DEMO_PASSWORD", default=None)
        if not password:
            raise CommandError("Set DEMO_PASSWORD in .env first.")

        if reset:
            Venue.objects.all().delete()

        types = {n: EventType.objects.get_or_create(name=n, defaults={"slug": slugify(n)})[0] for n in EVENT_TYPES}
        amen = {n: Amenity.objects.get_or_create(name=n, defaults={"slug": slugify(n)})[0] for n in AMENITIES}

        owner = self._user("owner@demo.yetyideges.test", "Selam", "Tesfaye", User.Role.OWNER, password)
        guest = self._user("guest@demo.yetyideges.test", "Abebe", "Kebede", User.Role.GUEST, password)
        guest2 = self._user("hana@demo.yetyideges.test", "Hana", "Girma", User.Role.GUEST, password)

        today = timezone.localdate()
        for i, v in enumerate(VENUES):
            venue, created = Venue.objects.get_or_create(
                name=v["name"],
                defaults=dict(
                    owner=owner, city=v["city"], area=v["area"], tagline=v["tagline"],
                    description=v["desc"], latitude=Decimal(v["lat"]), longitude=Decimal(v["lng"]),
                    capacity_min=v["cap"][0], capacity_max=v["cap"][1], price_per_day=v["price"],
                    rental_policies="50% deposit to confirm. Free cancellation up to 30 days before the event. "
                                    "Music until 11 pm.",
                ),
            )
            if not created:
                continue
            venue.event_types.set([types[t] for t in v["types"]])
            venue.amenities.set([amen[a] for a in v["amen"]])

            # A past confirmed event with a review, an upcoming confirmed one, and a pending request.
            guests = v["cap"][0] + 10
            past = Booking.objects.create(
                venue=venue, guest=guest if i % 2 else guest2, event_date=today - timedelta(days=20 + i),
                guest_count=guests, status=Booking.Status.ACCEPTED, quoted_price=venue.price_per_day,
                responded_at=timezone.now(),
            )
            rating, text = REVIEWS[i % len(REVIEWS)]
            Review.objects.create(booking=past, venue=venue, author=past.guest, rating=rating, comment=text)
            Booking.objects.create(
                venue=venue, guest=guest2, event_date=today + timedelta(days=14 + i * 3),
                guest_count=guests, status=Booking.Status.ACCEPTED, quoted_price=venue.price_per_day,
                responded_at=timezone.now(),
            )
            Booking.objects.create(
                venue=venue, guest=guest, event_date=today + timedelta(days=30 + i * 2),
                guest_count=guests, quoted_price=venue.price_per_day,
                event_type=types[v["types"][0]], message="Hi! Is this date available for our family event?",
            )

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {Venue.objects.count()} venues, {Booking.objects.count()} bookings. "
            "Log in with the demo accounts listed in this command's docstring (password = DEMO_PASSWORD in .env)."
        ))

    def _user(self, email, first, last, role, password):
        user, created = User.objects.get_or_create(
            email=email, defaults=dict(first_name=first, last_name=last, role=role)
        )
        if created:
            user.set_password(password)
            user.save()
        return user
