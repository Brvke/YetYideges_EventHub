#!/usr/bin/python3
"""contains the BaseModel class"""
import json
import os
import uuid
from datetime import datetime

class BaseModel:
    """Base class for all models."""
    def __init__(self, *args, **kwargs):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        for key, value in kwargs.items():
            setattr(self, key, value)
        if 'created_at' in kwargs:
            self.created_at = datetime.fromisoformat(kwargs['created_at'])
        if 'updated_at' in kwargs:
            self.updated_at = datetime.fromisoformat(kwargs['updated_at'])

    def save(self):
        """Saves the current state of the object."""
        self.updated_at = datetime.now()
        file_name = f"{self.__class__.__name__.lower()}s.json"
        data = self.load_data(file_name)
        data.append(self.to_dict())
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=4)

    def to_dict(self):
        """Converts the object to a dictionary."""
        result = self.__dict__.copy()
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result

    @classmethod
    def load_data(cls, file_name):
        """Loads the list of objects from a JSON file."""
        if not os.path.exists(file_name):
            return []
        with open(file_name, 'r') as file:
            return json.load(file)

    @classmethod
    def load(cls, file_name):
        """Loads the objects from a JSON file and creates instances."""
        data = cls.load_data(file_name)
        return [cls(**item) for item in data]
