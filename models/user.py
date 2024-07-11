#!/usr/bin/python3
""" holds class User"""
from hashlib import md5
from models.base_model import BaseModel
import models
import re
from datetime import datetime
import uuid
class User(BaseModel):
    """Representation of a User."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.email = kwargs.get('email')
        self._password = None
        self.__setattr__(kwargs.get('password', ''))
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.__class__ = 'User'
        

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

    def save(self):
        """Override save method to include additional validation."""
        if not self.validate_email(self.email):
            raise ValueError("Invalid email format")
        super().save()