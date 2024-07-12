#!/usr/bin/python3
""" Flask Application """
from models import FileStorage
from api.views import app_views
from flask import Flask, render_template, make_response, json, jsonify
from flask_cors import CORS
from flasgger import Swagger
from flasgger.utils import swag_from
from flask import current_app as app

import os 

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.register_blueprint(app_views)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.errorhandler(404)
def not_found(error):
    """ 404 Error
    ---
    responses:
        404:
        description: a resource was not found
    """
    return make_response(jsonify({'error': "Not found"}), 404)
app.config['SWAGGER'] = {
    'title': 'YetYideges EventHub API',
    'uiversion': 3
}

@app.route('/', methods=['GET'])
def index():
    # Convert all Venues to list of dictionaries
    with open('./storage/venue.json', 'r') as file:
        venues = json.load(file)
    return render_template('index.html', venues=venues)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/home')
def home() :
    return render_template('home.html')

@app.route('/venues')
def venues():
    with open('./storage/venue.json', 'r') as file:
        venues = json.load(file)
    return render_template('venues.html', venues=venues)

@app.route('/contact')
def contact():
    return render_template('contact.html')


    
Swagger(app)


if __name__ == "__main__":
    """ Main Function """
    app.run(host='0.0.0.0', port='5000', threaded=True, debug=True)
