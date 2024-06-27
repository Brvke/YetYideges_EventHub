#!/usr/bin/python3
from models.base_model import BaseModel

class Location(BaseModel):
    """Represents a location in the application"""
    name = ""
    address = ""
    latitude = 0.0
    longitude = 0.0
    venue_id = ""  # Google Place ID for detailed information

    def __init__(self, *args, **kwargs):
        """Initialize a location"""
        super().__init__(*args, **kwargs)
