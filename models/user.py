#!/usr/bin/python3
""" holds class User"""
from hashlib import md5
from models.base_model import BaseModel
import models
import re

class User(BaseModel):
    """Representation of a User."""
    
    def __init__(self, *args, **kwargs):
        """Initializes User."""
        self.email = ""
        self._password = ""  # Private attribute for storing hashed password
        self.first_name = ""
        self.last_name = ""
        self.phone_number = ""
        self.venues = []  # Assuming this will hold a list of place IDs
        self.reviews = []  # Assuming this will hold a list of review IDs
        super().__init__(*args, **kwargs)
        self.venues = kwargs.get('venues', [])
        self.reviews = kwargs.get('reviews', [])

    @property
    def password(self):
        """Password property getter."""
        return self._password

    def __setattr__(self, name, value):
        """Sets a password with MD5 encryption."""
        if name == "password":
            value = md5(value.encode()).hexdigest()
        super().__setattr__(name, value)

    def authenticate(self, email, password):
        """Authenticates the user."""
        stored_password_hash = md5(password.encode()).hexdigest()
        return self.email == email and self.password == stored_password_hash

    def to_dict(self):
        """Converts the User object to a dictionary, excluding sensitive info."""
        result = super().to_dict()
        result.pop('_password', None)  # Remove the internal password attribute
        return result

    @staticmethod
    def validate_email(email):
        """Validates the format of the email address by using regular expression."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone_number):
        """Validates the phone number format (e.g., E.164)."""
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, phone_number) is not None

    def save(self):
        """Override save method to include additional validation."""
        if not self.validate_email(self.email):
            raise ValueError("Invalid email format")
        if self.phone_number and not self.validate_phone(self.phone_number):
            raise ValueError("Invalid phone number format")
        super().save()