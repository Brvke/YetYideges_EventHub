#!/usr/bin/python3
""" objects that handle all default RestFul API actions for Venue - Review """
from models.venue import Venue
from models.amenity import Review
from models import storage
from api.views import app_views
from os import environ
from flask import abort, jsonify, make_response, request
from flasgger.utils import swag_from

@app_views.route('/venues/<venue_id>/reviews', methods=['GET'], strict_slashes=False)
def get_reviews_for_venue(venue_id):
    """Retrieves all reviews associated with a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    return jsonify([review.to_dict() for review in venue.reviews]), 200

@app_views.route('/venues/<venue_id>/reviews/<review_id>', methods=['GET'], strict_slashes=False)
def get_review_for_venue(venue_id, review_id):
    """Retrieves a specific review associated with a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    review = next((review for review in venue.reviews if review.id == review_id), None)
    if not review:
        abort(404, description="Review not found")

    return jsonify(review.to_dict()), 200

@app_views.route('/venues/<venue_id>/reviews', methods=['POST'], strict_slashes=False)
def create_review_for_venue(venue_id):
    """Creates a new review for a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    if not request.get_json():
        abort(400, description="Invalid JSON")

    data = request.get_json()
    if 'rating' not in data or 'comment' not in data:
        abort(400, description="Missing required fields")

    review = Review(**data)
    review.venue_id = venue.id
    review.save()

    return jsonify(review.to_dict()), 201

@app_views.route('/venues/<venue_id>/reviews/<review_id>', methods=['PUT'], strict_slashes=False)
def update_review_for_venue(venue_id, review_id):
    """Updates an existing review associated with a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    review = next((review for review in venue.reviews if review.id == review_id), None)
    if not review:
        abort(404, description="Review not found")

    if not request.get_json():
        abort(400, description="Invalid JSON")

    data = request.get_json()
    for key, value in data.items():
        setattr(review, key, value)
    review.save()

    return jsonify(review.to_dict()), 200

@app_views.route('/venues/<venue_id>/reviews/<review_id>', methods=['DELETE'], strict_slashes=False)
def delete_review_for_venue(venue_id, review_id):
    """Deletes a specific review associated with a venue."""
    venue = storage.get(Venue, venue_id)
    if not venue:
        abort(404, description="Venue not found")

    review = next((review for review in venue.reviews if review.id == review_id), None)
    if not review:
        abort(404, description="Review not found")

    storage.delete(review)
    storage.save()

    return '', 204