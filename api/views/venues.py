#!/usr/bin/python3
""" Objects that handle all default RestFul API actions for Venues """
from models.venue import Venue, Location  # Import the Venue and Location models
from models.user import User
from models.amenity import Amenity
from models import storage  # Import storage engine
from api.views import app_views  # Import the Blueprint from app_views
from flask import abort, make_response, request, json
from flask.json import jsonify
from flasgger import swag_from  # Import the swag_from method for Swagger documentation
from flask import render_template  # For rendering HTML templates
@app_views.route('/venues', methods=['GET'], strict_slashes=False)
@swag_from('documentation/venue/get_venues.yml', methods=['GET'])
def get_venues():
    """
    Retrieves the list of all Venue objects
    """
    venues = [venue.to_dict() for venue in Venue.load('venues.json')]
    # Convert all Venues to list of dictionaries
    # Return a rendered template
    return render_template('venues.html', venues=venues)

@app_views.route('/venues/<venue_id>', methods=['GET'], strict_slashes=False)
@swag_from('documentation/venue/get_venue.yml', methods=['GET'])
def get_venue(venue_id):
    """
    Retrieves a Venue object by ID
    """
    venue = [Venue.get('venues.json', venue_id)]  # Get the Venue by ID
    if not venue:
        abort(404)  # If Venue not found, return 404

    # Return JSON response
    return render_template('venue_detail.html', venues=venue)

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
    return make_response(jsonify({}), 200)  # Return empty JSON response with 200 status

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
    date = data.get('date', None)  # Extract date from request
    event_type = data.get('event_type', None)  # Extract event_type from request

    if not data or not (locations or amenities or date or event_type):
        # Return all venues if no specific filter criteria are provided
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

    # Filter by date and event_type if provided
    if date or event_type:
        filtered_venues = []
        for venue in list_venues:
            # Assuming Venue model has attributes `event_dates` and `event_types` for simplicity
            if date and date not in venue.event_dates:
                continue
            if event_type and event_type not in venue.event_types:
                continue
            filtered_venues.append(venue)
        list_venues = filtered_venues

    result = [venue.to_dict() for venue in list_venues]
    for venue in result:
        venue.pop('amenities', None)  # Remove amenities for simplicity

    return jsonify(result)
@app_views.route('/featured-venues', methods=['GET'])
def get_featured_venues():
    """
    Retrieves the list of featured Venue objects with specific fields
    """
    with open('venues.json', 'r') as f:
        venues = json.load(f)
    
    featured_venues = [venue for venue in venues if venue['is_featured']]
    return featured_venues

@app_views.route('/venues/<venue_id>/locations', methods=['POST'], strict_slashes=False)
def create_location_for_venue(venue_id):
    """Creates a new location for a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    if not request.is_json:
        abort(400, description="Invalid JSON")

    data = request.get_json()
    if not all(key in data for key in ('latitude', 'longitude')):
        abort(400, description="Missing required fields: latitude, longitude")

    location = Location(venue_id=venue_id, **data)
    location.save()

    return jsonify(location.to_dict()), 201
