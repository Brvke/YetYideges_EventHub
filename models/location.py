#!/usr/bin/python3
"""Location Model that inherits from BaseModel"""
from models.base_model import BaseModel  # Assuming BaseModel is in models/base_model.py
import json
import os

class Location(BaseModel):
    """Location class that represents a location in the application"""
    
    def __init__(self, *args, **kwargs):
        """Initialize Location instance"""
        self.address = kwargs.get('address', "")
        self.latitude = kwargs.get('latitude', 0.0)
        self.longitude = kwargs.get('longitude', 0.0)
        self.venue_id = kwargs.get('venue_id', None)  # Relates Location to a specific Venue
        super().__init__(*args, **kwargs)

    def to_dict(self):
        """Convert Location instance to dictionary format"""
        result = super().to_dict()
        result['address'] = self.address
        result['latitude'] = self.latitude
        result['longitude'] = self.longitude
        result['venue_id'] = self.venue_id
        return result

    def save(self):
        """Saves the current state of the Location object"""
        super().save()

    @staticmethod
    def get_by_id(location_id):
        """Static method to get a Location by its ID"""
        file_name = "locations.json"
        locations = BaseModel.load_data(file_name)
        for location_data in locations:
            if location_data['id'] == location_id:
                return Location(**location_data)
        return None

    @staticmethod
    def get_by_venue_id(venue_id):
        """Static method to get all Location instances by venue_id"""
        file_name = "locations.json"
        locations = BaseModel.load_data(file_name)
        return [Location(**location_data) for location_data in locations if location_data['venue_id'] == venue_id]
