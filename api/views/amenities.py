#!/usr/bin/python3
"""Objects that handle all default RestFul API actions for Amenities"""
from models.amenity import Amenity  # Import the Amenity model
from models import storage  # Import storage engine
from api.views import app_views  # Import the Blueprint from app_views
from flask import abort, jsonify, make_response, request  # Flask imports
from flasgger.utils import swag_from  # For API documentation with Swagger

@app_views.route('/amenities', methods=['GET'], strict_slashes=False)
@swag_from('documentation/amenity/all_amenities.yml')
def get_amenities():
    """
    Retrieves a list of all amenities
    """
    all_amenities = storage.all(Amenity).values()  # Get all Amenity objects
    list_amenities = [amenity.to_dict() for amenity in all_amenities]  # Convert to list of dictionaries
    return jsonify(list_amenities)  # Return JSON response

@app_views.route('/amenities/<amenity_id>/', methods=['GET'], strict_slashes=False)
@swag_from('documentation/amenity/get_amenity.yml', methods=['GET'])
def get_amenity(amenity_id):
    """Retrieves an amenity by its ID"""
    amenity = storage.get(Amenity, amenity_id)  # Get specific Amenity by ID
    if not amenity:
        abort(404)  # If not found, return 404

    return jsonify(amenity.to_dict())  # Return JSON response

@app_views.route('/amenities/<amenity_id>', methods=['DELETE'], strict_slashes=False)
@swag_from('documentation/amenity/delete_amenity.yml', methods=['DELETE'])
def delete_amenity(amenity_id):
    """
    Deletes an amenity object
    """
    amenity = storage.get(Amenity, amenity_id)  # Get specific Amenity by ID
    if not amenity:
        abort(404)  # If not found, return 404

    storage.delete(amenity)  # Delete the Amenity
    storage.save()  # Save the changes to the database
    return make_response(jsonify({}), 200)  # Return empty JSON with 200 status

@app_views.route('/amenities', methods=['POST'], strict_slashes=False)
@swag_from('documentation/amenity/post_amenity.yml', methods=['POST'])
def post_amenity():
    """
    Creates a new amenity
    """
    if not request.get_json():
        abort(400, description="Not a JSON")  # Return 400 if not JSON

    if 'name' not in request.get_json():
        abort(400, description="Missing name")  # Return 400 if 'name' is missing

    data = request.get_json()  # Get the JSON data from the request
    instance = Amenity(**data)  # Create a new Amenity instance
    instance.save()  # Save the instance to the database
    return make_response(jsonify(instance.to_dict()), 201)  # Return the new Amenity in JSON with 201 status

@app_views.route('/amenities/<amenity_id>', methods=['PUT'], strict_slashes=False)
@swag_from('documentation/amenity/put_amenity.yml', methods=['PUT'])
def put_amenity(amenity_id):
    """
    Updates an existing amenity
    """
    if not request.get_json():
        abort(400, description="Not a JSON")  # Return 400 if not JSON

    ignore = ['id', 'created_at', 'updated_at']  # Fields to ignore when updating

    amenity = storage.get(Amenity, amenity_id)  # Get specific Amenity by ID
    if not amenity:
        abort(404)  # If not found, return 404

    data = request.get_json()  # Get the JSON data from the request
    for key, value in data.items():
        if key not in ignore:
            setattr(amenity, key, value)  # Update the Amenity attributes
    storage.save()  # Save the changes to the database
    return make_response(jsonify(amenity.to_dict()), 200)  # Return the updated Amenity in JSON with 200 status
