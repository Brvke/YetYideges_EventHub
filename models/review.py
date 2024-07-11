#!/usr/bin/python3
"""Review Model that inherits from BaseModel"""
from models.base_model import BaseModel
import os
import json

class Review(BaseModel):
    """Review class that represents a review in the application"""

    def __init__(self, *args, **kwargs):
        """Initialize Review instance"""
        self.user_id = kwargs.get('user_id', "")
        self.venue_id = kwargs.get('venue_id', "")
        self.rating = kwargs.get('rating', 0)
        self.comment = kwargs.get('comment', "")
        super().__init__(*args, **kwargs)

    def to_dict(self):
        """Convert Review instance to dictionary format"""
        result = super().to_dict()
        result['user_id'] = self.user_id
        result['venue_id'] = self.venue_id
        result['rating'] = self.rating
        result['comment'] = self.comment
        return result

    def save(self):
        """Saves the current state of the Review object"""
        super().save()

    @staticmethod
    def get_by_id(review_id):
        """Static method to get a Review by its ID"""
        file_name = "reviews.json"
        reviews = BaseModel.load_data(file_name)
        for review_data in reviews:
            if review_data['id'] == review_id:
                return Review(**review_data)
        return None

    @classmethod
    def load(cls, file_name):
        """Loads reviews from a JSON file"""
        reviews = []
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                reviews_data = json.load(f)
                for review_data in reviews_data:
                    reviews.append(cls(**review_data))
        return reviews

    def save_to_file(self, file_name):
        """Saves the review to a JSON file"""
        reviews = self.load(file_name)
        reviews.append(self)
        reviews_data = [review.to_dict() for review in reviews]
        with open(file_name, 'w') as f:
            json.dump(reviews_data, f, indent=4)
