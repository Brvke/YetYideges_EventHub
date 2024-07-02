#!/usr/bin/python3
"""RESTful API actions for Reviews"""
from models.review import Review  # Import the Review model
from models.user import User  # Import the User model for validation
from models.venue import Venue  # Import the Venue model for validation
from models import storage  # Import storage engine
from api.views import app_views  # Import the Blueprint from app_views
from flask import abort, jsonify, make_response, request  # Flask imports
from flasgger.utils import swag_from  # For API documentation with Swagger

@app_views.route('/reviews', methods=['GET'], strict_slashes=False)
@swag_from('documentation/review/get_reviews.yml', methods=['GET'])
def get_reviews():
    """
    Retrieves the list of all reviews
    """
    all_reviews = storage.all(Review).values()  # Get all Review objects
    list_reviews = [review.to_dict() for review in all_reviews]  # Convert to list of dictionaries
    return jsonify(list_reviews)  # Return JSON response

@app_views.route('/reviews/<review_id>', methods=['GET'], strict_slashes=False)
@swag_from('documentation/review/get_review.yml', methods=['GET'])
def get_review(review_id):
    """
    Retrieves a review by its ID
    """
    review = storage.get(Review, review_id)  # Get specific Review by ID
    if not review:
        abort(404)  # If not found, return 404

    return jsonify(review.to_dict())  # Return JSON response

@app_views.route('/reviews', methods=['POST'], strict_slashes=False)
@swag_from('documentation/review/post_review.yml', methods=['POST'])
def post_review():
    """
    Creates a new review
    """
    if not request.get_json():
        abort(400, description="Not a JSON")  # Return 400 if not JSON

    data = request.get_json()  # Get the JSON data from the request

    if 'user_id' not in data:
        abort(400, description="Missing user_id")  # Return 400 if 'user_id' is missing

    user = storage.get(User, data['user_id'])  # Verify User exists
    if not user:
        abort(404, description="User not found")  # If User not found, return 404

    if 'venue_id' not in data:
        abort(400, description="Missing venue_id")  # Return 400 if 'venue_id' is missing

    venue = storage.get(Venue, data['venue_id'])  # Verify Venue exists
    if not venue:
        abort(404, description="Venue not found")  # If Venue not found, return 404

    if 'rating' not in data or not (1 <= data['rating'] <= 5):
        abort(400, description="Invalid or missing rating")  # Return 400 if 'rating' is missing or invalid

    if 'text' not in data:
        abort(400, description="Missing text")  # Return 400 if 'text' is missing

    review = Review(**data)  # Create a new Review instance
    review.save()  # Save the Review to the database
    return make_response(jsonify(review.to_dict()), 201)  # Return the new Review in JSON with 201 status

@app_views.route('/reviews/<review_id>', methods=['PUT'], strict_slashes=False)
@swag_from('documentation/review/put_review.yml', methods=['PUT'])
def put_review(review_id):
    """
    Updates an existing review
    """
    review = storage.get(Review, review_id)  # Get specific Review by ID
    if not review:
        abort(404)  # If not found, return 404

    if not request.get_json():
        abort(400, description="Not a JSON")  # Return 400 if not JSON

    ignore = ['id', 'user_id', 'venue_id', 'created_at', 'updated_at']  # Fields to ignore when updating

    data = request.get_json()  # Get the JSON data from the request
    for key, value in data.items():
        if key not in ignore:
            setattr(review, key, value)  # Update the Review attributes
    storage.save()  # Save the changes to the database
    return make_response(jsonify(review.to_dict()), 200)  # Return the updated Review in JSON with 200 status

@app_views.route('/reviews/<review_id>', methods=['DELETE'], strict_slashes=False)
@swag_from('documentation/review/delete_review.yml', methods=['DELETE'])
def delete_review(review_id):
    """
    Deletes a review by ID
    """
    review = storage.get(Review, review_id)  # Get specific Review by ID
    if not review:
        abort(404)  # If not found, return 404

    storage.delete(review)  # Delete the Review
    storage.save()  # Save the changes to the database
    return make_response(jsonify({}), 200)  # Return empty JSON with 200 status