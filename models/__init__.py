#!/usr/bin/python3
"""
Initialize the models package for JSON storage.
"""

from models.engines.file_storage import FileStorage

# Initialize the storage with FileStorage
storage = FileStorage()

# Load existing data from the JSON file into storage
storage.reload()
