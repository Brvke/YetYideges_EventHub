#!/usr/bin/python3
"""
File storage engine for handling JSON storage of models.
"""
import json
import os
import models
from models.base_model import BaseModel

class FileStorage:
    """Serializes instances to a JSON file & deserializes back to instances."""
    __file_path = "data.json"  # Path to the JSON file to store data
    __objects = {}  # A dictionary to store all objects by class name and ID

    def all(self):
        """Returns the dictionary of all stored objects."""
        return self.__objects

    def new(self, obj):
        """Adds a new object to the storage dictionary."""
        key = f"{obj.__class__.__name__}.{obj.id}"
        self.__objects[key] = obj

    def save(self):
        """Serializes the storage dictionary to the JSON file."""
        obj_dict = {key: obj.to_dict() for key, obj in self.__objects.items()}
        with open(self.__file_path, 'w') as file:
            json.dump(obj_dict, file, indent=4)

    def reload(self):
        """Deserializes the JSON file to the storage dictionary."""
        if os.path.exists(self.__file_path):
            with open(self.__file_path, 'r') as file:
                obj_dict = json.load(file)
                for key, obj_data in obj_dict.items():
                    class_name = obj_data['__class__']
                    cls = self._get_class_from_name(class_name)
                    if cls:
                        obj = cls(**obj_data)
                        self.__objects[key] = obj
                        
                        if class_name == 'Venue' and 'location_ids' in obj_data:
                            obj.location_ids = obj_data['location_ids']


    def delete(self, obj=None):
        """Deletes obj from __objects if its inside."""
        if obj is not None:
            key = f"{obj.__class__.__name__}.{obj.id}"
            if key in self.__objects:
                del self.__objects[key]

    def close(self):
        """Calls reload method for deserializing the JSON file to objects."""
        self.reload()

    def _get_class_from_name(self, class_name):
        """Retrieves a class from its name for object instantiation."""
        try:
            from models.user import User
            from models.venue import Venue
            from models.amenity import Amenity
            from models.review import Review
            from models.location import Location
            from models.engines.file_storage import FileStorage
            classes = {
                "User": User,
                "Venue": Venue,
                "Amenity": Amenity,
                "Review": Review,
                "Location": Location,
                "FileStorage": FileStorage
            }
            return classes[class_name]
        except ImportError:
            return None
