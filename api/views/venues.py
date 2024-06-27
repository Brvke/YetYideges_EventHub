#!/usr/bin/python3
""" Objects that handle all default RestFul API actions for Venues """
from models.venue import Venue  # Import the Venue model
from models.user import User
from models.amenity import Amenity
from models import storage  # Import storage engine
from api.views import app_views  # Import the Blueprint from app_views
from flask import abort, jsonify, make_response, request  # Flask imports
from flasgger.utils import swag_from  # For API documentation with Swagger

@app_views.route('/venues', methods=['GET'], strict_slashes=False)
@swag_from('documentation/venue/get_venues.yml', methods=['GET'])
def get_venues():
    """
    Retrieves the list of all Venue objects
    """
    venues = [venue.to_dict() for venue in storage.all(Venue).values()]  # Convert all Venues to list of dictionaries
    return jsonify(venues)  # Return JSON response

@app_views.route('/venues/<venue_id>', methods=['GET'], strict_slashes=False)
@swag_from('documentation/venue/get_venue.yml', methods=['GET'])
def get_venue(venue_id):
    """
    Retrieves a Venue object by ID
    """
    venue = storage.get(Venue, venue_id)  # Get the Venue by ID
    if not venue:
        abort(404)  # If Venue not found, return 404

    return jsonify(venue.to_dict())  # Return JSON response

@app_views.route('/venues/<venue_id>', methods=['DELETE'], strict_slashes=False)
@swag_from('documentation/venue/delete_venue.yml', methods=['DELETE'])
def delete_venue(venue_id):
    """
    Deletes a Venue object by ID
    """
    venue = storage.get(Venue, venue_id)  # Get the Venue by ID
    if not venue:
        abort(404)  # If Venue not found, return 404

    storage.delete(venue)  # Delete the Venue
    storage.save()  # Save changes to the storage
    return make_response(jsonify({}), 200)  # Return empty JSON with 200 status

@app_views.route('/venues', methods=['POST'], strict_slashes=False)
@swag_from('documentation/venue/post_venue.yml', methods=['POST'])
def post_venue():
    """
    Creates a Venue
    """
    if not request.get_json():
        abort(400, description="Not a JSON")  # Return 400 if not JSON

    data = request.get_json()

    if 'user_id' not in data:
        abort(400, description="Missing user_id")  # Return 400 if 'user_id' is missing

    user = storage.get(User, data['user_id'])  # Verify User exists
    if not user:
        abort(404)  # If User not found, return 404

    if 'name' not in data:
        abort(400, description="Missing name")  # Return 400 if 'name' is missing

    if 'location' not in data:
        abort(400, description="Missing location")  # Return 400 if 'location' is missing

    venue = Venue(**data)  # Create a new Venue instance
    venue.save()  # Save the Venue to the storage
    return make_response(jsonify(venue.to_dict()), 201)  # Return the new Venue in JSON with 201 status

@app_views.route('/venues/<venue_id>', methods=['PUT'], strict_slashes=False)
@swag_from('documentation/venue/put_venue.yml', methods=['PUT'])
def put_venue(venue_id):
    """
    Updates a Venue object by ID
    """
    venue = storage.get(Venue, venue_id)  # Get the Venue by ID
    if not venue:
        abort(404)  # If Venue not found, return 404

    data = request.get_json()
    if not data:
        abort(400, description="Not a JSON")  # Return 400 if not JSON

    ignore = ['id', 'user_id', 'created_at', 'updated_at']  # Fields to ignore

    for key, value in data.items():
        if key not in ignore:
            setattr(venue, key, value)  # Update Venue attributes
    storage.save()  # Save changes to the storage
    return make_response(jsonify(venue.to_dict()), 200)  # Return the updated Venue in JSON with 200 status

@app_views.route('/venues_search', methods=['POST'], strict_slashes=False)
@swag_from('documentation/venue/post_search.yml', methods=['POST'])
def venues_search():
    """
    Retrieves all Venue objects depending on the JSON in the request body
    """

    if not request.get_json():
        abort(400, description="Not a JSON")  # Return 400 if not JSON

    data = request.get_json()

    locations = data.get('locations', [])
    amenities = data.get('amenities', [])

    if not data or not (locations or amenities):
        # Return all venues if no specific filter criteria are provided
        venues = storage.all(Venue).values()
        return jsonify([venue.to_dict() for venue in venues])

    list_venues = []

    if locations:
        # Filter venues by location
        for venue in storage.all(Venue).values():
            if venue.location in locations:
                list_venues.append(venue)

    if amenities:
        if not list_venues:
            list_venues = storage.all(Venue).values()
        amenities_objs = [storage.get(Amenity, amenity_id) for amenity_id in amenities]
        list_venues = [venue for venue in list_venues if all(amenity in venue.amenities for amenity in amenities_objs)]

    result = [venue.to_dict() for venue in list_venues]
    for venue in result:
        venue.pop('amenities', None)  # Remove amenities for simplicity

    return jsonify(result)
