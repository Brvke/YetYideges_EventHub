#!/usr/bin/python3
""" Flask Application """
from models import storage
from models.venue import Venue
from api.views import app_views
from os import environ
from flask import Flask, render_template, make_response, json, jsonify
from flask_cors import CORS
from flasgger import Swagger
from flasgger.utils import swag_from

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.register_blueprint(app_views)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.teardown_appcontext
def close_db(error):
    """ Close Storage """
    storage.close()


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
def start():
    venues = [venue.to_dict() for venue in Venue.load('venue.json')
              ]  # Convert all Venues to list of dictionaries
    with open('/mnt/c/Users/test/Documents/alx_se_brvke/YetYideges_EventHub/api/venue.json', 'r') as file:
        venues = json.load(file)
    return render_template('yet1.html', venues=venues)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/venues')
def venues():
    with open('/mnt/c/Users/test/Documents/alx_se_brvke/YetYideges_EventHub/api/venue.json', 'r') as file:
        venues = json.load(file)
    return render_template('venues.html', venues=venues)
    
Swagger(app)


if __name__ == "__main__":
    """ Main Function """
    app.run(host='0.0.0.0', port='5000', threaded=True, debug=True)