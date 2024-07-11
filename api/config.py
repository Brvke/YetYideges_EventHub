import os

# Define the base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Path to the JSON storage file
JSON_FILE_PATHS = [
    os.path.join(BASE_DIR, 'storage', 'venue.json'),
    os.path.join(BASE_DIR, 'storage', 'data.json'),
    os.path.join(BASE_DIR, 'storage', 'file3.json'),
    # Add more file paths as needed
]

# Paths to static and template directories
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
