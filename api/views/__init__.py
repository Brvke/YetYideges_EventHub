#!/usr/bin/python3
""" Blueprint for API """
from flask import Blueprint

app_views = Blueprint('app_views', __name__, url_prefix='/api')

#from api.views.index import *
from api.views.venues import *
#from api.views.venues_reviews import *
#from api.views.venues_amenities import *
from api.views.amenities import *
from api.views.users import *
from api.views.reviews import *