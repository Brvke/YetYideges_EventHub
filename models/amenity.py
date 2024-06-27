#!/usr/bin/python
""" holds class Amenity"""
import models
from models.base_model import BaseModel

class Amenity(BaseModel):
    """Representation of an Amenity for Event Hub Rentals"""
    # Directly defining attributes for JSON storage
    name = ""

    def __init__(self, *args, **kwargs):
        """Initializes Amenity"""
        super().__init__(*args, **kwargs)
