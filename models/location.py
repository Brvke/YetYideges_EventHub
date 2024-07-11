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

    @classmethod
    def load(cls, file_name):
        """Loads locations from a JSON file"""
        locations = []
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                locations_data = json.load(f)
                for location_data in locations_data:
                    locations.append(cls(**location_data))
        return locations

    def save_to_file(self, file_name):
        """Saves the location to a JSON file"""
        locations = self.load(file_name)
        locations.append(self)
        locations_data = [location.to_dict() for location in locations]
        with open(file_name, 'w') as f:
            json.dump(locations_data, f, indent=4)
