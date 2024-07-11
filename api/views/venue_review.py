#!/usr/bin/python3
""" Objects that handle all default RestFul API actions for Venue - Location """
from models.venue import Venue
from models.location import Location
from models import storage
from api.views import app_views
from flask import abort, jsonify, make_response, request
from flasgger.utils import swag_from

@app_views.route('/venues/<venue_id>/locations', methods=['GET'], strict_slashes=False)
@swag_from('documentation/location/get_locations.yml', methods=['GET'])
def get_locations_for_venue(venue_id):
    """ Retrieves all locations associated with a venue. """
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    return jsonify([location.to_dict() for location in venue.locations]), 200

@app_views.route('/venues/<venue_id>/locations/<location_id>', methods=['GET'], strict_slashes=False)
@swag_from('documentation/location/get_location.yml', methods=['GET'])
def get_location_for_venue(venue_id, location_id):
    """ Retrieves a specific location associated with a venue. """
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    location = next((location for location in venue.locations if location.id == location_id), None)
    if not location:
        abort(404, description="Location not found")

    return jsonify(location.to_dict()), 200

@app_views.route('/venues/<venue_id>/locations', methods=['POST'], strict_slashes=False)
@swag_from('documentation/location/post_location.yml', methods=['POST'])
def create_location_for_venue(venue_id):
    """ Creates a new location for a venue. """
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    if not request.get_json():
        abort(400, description="Invalid JSON")

    data = request.get_json()
    if 'latitude' not in data or 'longitude' not in data:
        abort(400, description="Missing required fields: latitude and/or longitude")

    location = Location(**data)
    location.venue_id = venue.id
    location.save()

    return jsonify(location.to_dict()), 201

@app_views.route('/venues/<venue_id>/locations/<location_id>', methods=['PUT'], strict_slashes=False)
@swag_from('documentation/location/put_location.yml', methods=['PUT'])
def update_location_for_venue(venue_id, location_id):
    """ Updates an existing location associated with a venue. """
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    location = next((location for location in venue.locations if location.id == location_id), None)
    if not location:
        abort(404, description="Location not found")

    if not request.get_json():
        abort(400, description="Invalid JSON")

    data = request.get_json()
    for key, value in data.items():
        setattr(location, key, value)
    location.save()

    return jsonify(location.to_dict()), 200

@app_views.route('/venues/<venue_id>/locations/<location_id>', methods=['DELETE'], strict_slashes=False)
@swag_from('documentation/location/delete_location.yml', methods=['DELETE'])
def delete_location_for_venue(venue_id, location_id):
    """ Deletes a specific location associated with a venue. """
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    location = next((location for location in venue.locations if location.id == location_id), None)
    if not location:
        abort(404, description="Location not found")

    storage.delete(location)
    storage.save()

    return '', 204
