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

    def __init__(self, *args, **kwargs):
        """Initializes EventHubPlace."""
        super().__init__(*args, **kwargs)
        self.amenities = []  # Initialize amenities as a list
        self.locations = []  # Initialize locations as a list

    @property
    def reviews(self):
        """Getter attribute returns the list of Review instances related to the venue."""
        return [review for review in models.storage.all(Review).values() if review.venue_id == self.id]

    @property
    def amenities(self):
        """Getter attribute returns the list of Amenity instances related to the venue."""
        return [amenity for amenity in models.storage.all(Amenity).values() if amenity.id in self.amenity_ids]

    @property
    def locations(self):
        """Getter attribute returns the list of Location instances related to the venue."""
        return [location for location in models.storage.all(Location).values() if location.id in self.location_ids]

    def to_dict(self):
        """Converts the Venue object to a dictionary."""
        result = super().to_dict()
        result['amenities'] = [amenity.to_dict() for amenity in self.amenities]
        result['locations'] = [location.to_dict() for location in self.locations]
        result.pop('amenity_ids', None)
        result.pop('location_ids', None)
        return result