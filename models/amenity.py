#!/usr/bin/python3
"""Amenity Model that inherits from BaseModel"""
from models.base_model import BaseModel
import os
import json

class Amenity(BaseModel):
    """Amenity class that represents an amenity in the application"""

    def __init__(self, *args, **kwargs):
        """Initialize Amenity instance"""
        self.name = kwargs.get('name', "")
        self.description = kwargs.get('description', "")
        super().__init__(*args, **kwargs)

    def to_dict(self):
        """Convert Amenity instance to dictionary format"""
        result = super().to_dict()
        result['name'] = self.name
        result['description'] = self.description
        return result

    def save(self):
        """Saves the current state of the Amenity object"""
        super().save()

    @staticmethod
    def get_by_id(amenity_id):
        """Static method to get an Amenity by its ID"""
        file_name = "amenities.json"
        amenities = BaseModel.load_data(file_name)
        for amenity_data in amenities:
            if amenity_data['id'] == amenity_id:
                return Amenity(**amenity_data)
        return None

    @classmethod
    def load(cls, file_name):
        """Loads amenities from a JSON file"""
        amenities = []
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                amenities_data = json.load(f)
                for amenity_data in amenities_data:
                    amenities.append(cls(**amenity_data))
        return amenities

    def save_to_file(self, file_name):
        """Saves the amenity to a JSON file"""
        amenities = self.load(file_name)
        amenities.append(self)
        amenities_data = [amenity.to_dict() for amenity in amenities]
        with open(file_name, 'w') as f:
            json.dump(amenities_data, f, indent=4)
