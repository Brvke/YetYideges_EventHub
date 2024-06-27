#!/usr/bin/python3
"""RESTful API actions for Users"""
from models.user import User
from models import storage
from api.views import app_views
from flask import Flask, abort, jsonify, make_response, request


@app_views.route('/users', methods=['GET'])
def get_users():
    """Retrieves the list of all user objects."""
    all_users = storage.all(User).values()
    list_users = [user.to_dict() for user in all_users]
    return jsonify(list_users)

@app_views.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Retrieves a user by ID."""
    user = storage.all(User).get(f'User.{user_id}')
    if not user:
        abort(404)
    return jsonify(user.to_dict())

@app_views.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Deletes a user by ID."""
    user = storage.all(User).get(f'User.{user_id}')
    if not user:
        abort(404)
    storage.delete(user)
    storage.save()
    return make_response(jsonify({}), 200)

@app_views.route('/users', methods=['POST'])
def post_user():
    """Creates a new user."""
    if not request.get_json():
        abort(400, description="Not a JSON")
    data = request.get_json()
    if 'email' not in data:
        abort(400, description="Missing email")
    if 'password' not in data:
        abort(400, description="Missing password")
    user = User(**data)
    user.save()
    storage.new(user)
    storage.save()
    return make_response(jsonify(user.to_dict()), 201)

@app_views.route('/users/<user_id>', methods=['PUT'])
def put_user(user_id):
    """Updates an existing user."""
    user = storage.all(User).get(f'User.{user_id}')
    if not user:
        abort(404)
    if not request.get_json():
        abort(400, description="Not a JSON")
    data = request.get_json()
    ignore = ['id', 'email', 'created_at', 'updated_at']
    for key, value in data.items():
        if key not in ignore:
            setattr(user, key, value)
    user.save()
    storage.save()
    return make_response(jsonify(user.to_dict()), 200)