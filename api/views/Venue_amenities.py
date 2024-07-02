#!/usr/bin/python3
""" objects that handle all default RestFul API actions for Venue - Amenity """
from models.venue import Venue
from models.amenity import Amenity
from models import storage
from api.views import app_views
from os import environ
from flask import abort, jsonify, make_response, request
from flasgger.utils import swag_from

@app_views.route('/venues/<venue_id>/amenities/<amenity_id>', methods=['POST'], strict_slashes=False)
def associate_amenity_with_venue(venue_id, amenity_id):
    """Associates an amenity with a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    amenity = storage.get(Amenity, amenity_id)
    if not amenity:
        abort(404, description="Amenity not found")

    if amenity in venue.amenities:
        return jsonify(venue.to_dict()), 200  # Amenity already associated, return venue

    venue.amenities.append(amenity)
    storage.save()
    return jsonify(venue.to_dict()), 201

@app_views.route('/venues/<venue_id>/amenities/<amenity_id>', methods=['DELETE'], strict_slashes=False)
def disassociate_amenity_from_venue(venue_id, amenity_id):
    """Disassociates an amenity from a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    amenity = storage.get(Amenity, amenity_id)
    if not amenity:
        abort(404, description="Amenity not found")

    if amenity not in venue.amenities:
        return jsonify(venue.to_dict()), 200  # Amenity already not associated, return venue

    venue.amenities.remove(amenity)
    storage.save()
    return jsonify(venue.to_dict()), 200