#!/usr/bin/python
""" holds class Place"""

import models
from models.base_model import BaseModel
from models.amenity import Amenity
from models.review import Review

class Venue(BaseModel):
    """Representation of a venue/place for Event Hub Rentals."""
    user_id = ""
    name = ""
    description = ""
    price_by_night = 0
    location_ids = []
    latitude = 0.0
    longitude = 0.0
    amenities = []
    event_capacity = 0
    rental_policies = ""

    def __init__(self, *args, **kwargs):
        """Initializes EventHubPlace."""
        super().__init__(*args, **kwargs)
        if 'location_ids' not in self.__dict__:
            self.location_ids = []  # Initialize location_ids if not present
        if 'amenities' not in self.__dict__:
            self.amenities = []  # Initialize amenities if not present

    @property
    def reviews(self):
        """Getter attribute returns the list of Review instances related to the venue."""
        review_list = []
        all_reviews = models.storage.all(Review)
        for review in all_reviews.values():
            if review.venue_id == self.id:
                review_list.append(review)
        return review_list

    @property
    def amenities(self):
        """Getter attribute returns the list of Amenity instances related to the venue."""
        amenity_list = []
        all_amenities = models.storage.all(Amenity)
        for amenity in all_amenities.values():
            if amenity.id in self.amenity_ids:
                amenity_list.append(amenity)
        return amenity_list
    
    @property
    def locations(self):
        """Getter attribute that returns a list of Location instances related to the venue"""
        location_list = []
        for loc_id in self.location_ids:
            if models.storage.get(Location, loc_id):
                location_list.append(models.storage.get(Location, loc_id))
        return location_list
        
