#!/usr/bin/python3
"""Defines the Reservation class."""
from datetime import datetime
from models.base_model import BaseModel

class Reservation(BaseModel):
    """Representation of a Reservation."""
    user_id = ""
    place_id = ""
    start_time = datetime.now()
    end_time = datetime.now()
    total_cost = 0.0

    def __init__(self, *args, **kwargs):
        """Initializes Reservation."""
        super().__init__(*args, **kwargs)

    def calculate_total_cost(self, price_by_hour):
        """Calculates the total cost of the reservation."""
        duration = (self.end_time - self.start_time).total_seconds() / 3600  # Convert seconds to hours
        self.total_cost = duration * price_by_hour
