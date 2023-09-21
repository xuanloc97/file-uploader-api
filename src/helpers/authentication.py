"""
Create a function to check authentication for flask app
"""
import os
import jwt
import base64
from functools import wraps
from flask import request, jsonify

from src.api.models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'access-token' in request.headers:
            token = request.headers['access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, os.environ.get('SECRET_KEY'))
            current_user = User.query\
                .filter_by(public_id = data['public_id'])\
                .first()
        except:
            return jsonify({
                'message' : 'Token is invalid !'
            }), 401
        # returns the current logged in users context to the routes
        return  f(current_user, *args, **kwargs)
  
    return decorated
