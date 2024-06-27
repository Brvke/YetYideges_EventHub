#!/usr/bin/python3
""" holds class User"""
import models
from models.base_model import BaseModel
from hashlib import md5

class User(BaseModel):
    """Representation of a User."""
    email = ""
    password = ""
    first_name = ""
    last_name = ""
    phone_number = ""
    venues = []  # Assuming this will hold a list of place IDs
    reviews = []  # Assuming this will hold a list of review IDs

    def __init__(self, *args, **kwargs):
        """Initializes User."""
        super().__init__(*args, **kwargs)
        self.venues = kwargs.get('places', [])
        self.reviews = kwargs.get('reviews', [])

    def __setattr__(self, name, value):
        """Sets a password with MD5 encryption."""
        if name == "password":
            value = md5(value.encode()).hexdigest()
        super().__setattr__(name, value)

    def authenticate(self, email, password):
        """Authenticates the user."""
        stored_password_hash = md5(password.encode()).hexdigest()
        return self.email == email and self.password == stored_password_hash
