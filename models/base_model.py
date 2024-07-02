#!/usr/bin/python3
"""Enhanced BaseModel class for the event hub rental app"""
import json
import os
import uuid
from datetime import datetime

class BaseModel:
    """Base class for all models with enhanced features."""
    
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
        """Saves the current state of the object with better file management."""
        self.updated_at = datetime.now()
        file_name = f"{self.__class__.__name__.lower()}s.json"
        data = self.load_data(file_name)
        
        # Find existing entry in data to update
        existing = next((item for item in data if item['id'] == self.id), None)
        if existing:
            data.remove(existing)
        
        data.append(self.to_dict())
        
        # Write the entire data back to file
        try:
            with open(file_name, 'w') as file:
                json.dump(data, file, indent=4)
        except IOError as e:
            print(f"Error writing to file {file_name}: {e}")

    def to_dict(self):
        """Converts the object to a dictionary, including class name."""
        result = self.__dict__.copy()
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        result['__class__'] = self.__class__.__name__
        return result

    @classmethod
    def load_data(cls, file_name):
        """Loads the list of objects from a JSON file with error handling."""
        if not os.path.exists(file_name):
            return []
        try:
            with open(file_name, 'r') as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading from file {file_name}: {e}")
            return []

    @classmethod
    def load(cls, file_name):
        """Loads the objects from a JSON file and creates instances."""
        data = cls.load_data(file_name)
        return [cls(**item) for item in data]

    @classmethod
    def find_by_id(cls, file_name, obj_id):
        """Finds an object by its ID from a JSON file."""
        data = cls.load_data(file_name)
        for item in data:
            if item['id'] == obj_id:
                return cls(**item)
        return None

    def delete(self):
        """Deletes the current object from the JSON file."""
        file_name = f"{self.__class__.__name__.lower()}s.json"
        data = self.load_data(file_name)
        
        data = [item for item in data if item['id'] != self.id]
        
        try:
            with open(file_name, 'w') as file:
                json.dump(data, file, indent=4)
        except IOError as e:
            print(f"Error writing to file {file_name}: {e}")