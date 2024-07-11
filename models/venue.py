#!/usr/bin/python3
""" holds class Venue"""

import models
from models.base_model import BaseModel
from models.amenity import Amenity
from models.review import Review
from models.location import Location

class Venue(BaseModel):
    """Representation of a venue/place for Event Hub Rentals."""

    user_id = ""
    name = ""
    description = ""
    price_by_night = 0
    latitude = 0.0
    longitude = 0.0
    event_capacity = 0
    rental_policies = ""
    location_ids = []

    def __init__(self, *args, **kwargs):
        """Initializes EventHubPlace."""
        super().__init__(*args, **kwargs)
        self.location_ids = kwargs.get('location_ids', [])

    @property
    def reviews(self):
        """Getter attribute returns the list of Review instances related to the venue."""
        return [review for review in models.storage.all(Review).values() if review.venue_id == self.id]

    @property
    def locations(self):
        """Getter attribute returns the list of Location instances related to the venue."""
        return [location for location in models.storage.all(Location).values() if location.id in self.location_ids]

    def add_location(self, location):
        """Add a location to the venue."""
        if location.id not in self.location_ids:
            self.location_ids.append(location.id)
            location.venue_id = self.id
            location.save()
            self.save()

    def to_dict(self):
        """Converts the Venue object to a dictionary."""
        result = super().to_dict()
        result['location_ids'] = self.location_ids
        return result
