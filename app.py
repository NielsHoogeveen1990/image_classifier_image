from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
from api.classify.classify import get_prediction


app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.ImageDB
# Create collection "Users" in database
users = db["Users"]


def user_exists(username):
    if users.find({
        "Username": username
    }).count() != 0:
        return True
    else:
        return False


def verify_password(username, password):
    # Check if the username exists
    if not user_exists(username):
        return False

    hashed_password = users.find({
        "Username": username
    })[0]["Password"]

    # If the hashed password is correct return True
    if bcrypt.hashpw(password.encode('utf8'), hashed_password) == hashed_password:
        return True
    else:
        return False


def generate_return_dict(status, message):
    retJson = {
        "status": status,
        "message": message
    }
    return retJson


def verify_credentials(username, password):
    if not user_exists(username):
        return generate_return_dict(301, "Invalid username."), True

    correct_pw = verify_password(username, password)
    if not correct_pw:
        return generate_return_dict(302, "Invalid password."), True

    # If the username is valid and password correct, return None for message and False for error
    return None, False


class Welcome(Resource):
    def get(self):
        retJson = {
            "status": 200,
            "message": "Welcome to the image classifier API."
        }
        return jsonify(retJson)


class Register(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data["username"]
        password = posted_data["password"]

        if user_exists(username):
            retJson = {
                "status": 301,
                "message": "Username already exists."
            }
            return jsonify(retJson)

        hashed_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_password,
            "Tokens": 5
        })

        retJson = {
            "status": 200,
            "message": "Successfully signed up."
        }
        return jsonify(retJson)


class Classify(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data["username"]
        password = posted_data["password"]
        url = posted_data["url"]

        retJson, error = verify_credentials(username, password)
        if error==True:
            return jsonify(retJson)

        tokens = users.find({
            "Username": username
        })[0]["Tokens"]

        if tokens==0:
            return jsonify(generate_return_dict(303, "Not enough tokens."))

        # Get request from URL
        response = requests.get(url)
        # Get prediction from classify.py
        prediction = get_prediction(image__url_repsonse=response)

        retJson = {
                    "status": 200,
                    "Predicted class": prediction[1]
                }

        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": tokens - 1
            }
        })

        return jsonify(retJson)


class Refill(Resource):
    def post(self):
        posted_data = request.get_json()

        username = posted_data["username"]
        password = posted_data["password"]
        token_amount = posted_data["token_amount"]

        retJson, error = verify_credentials(username, password)
        if error == True:
            return jsonify(retJson)

        tokens = users.find({
            "Username": username
        })[0]["Tokens"]

        users.update({
            "Username": username
        },{
            "$set": {
                "Tokens": tokens + token_amount
            }
        })

        return jsonify(generate_return_dict(200, "Refilled successfully."))


api.add_resource(Welcome, '/welcome')
api.add_resource(Register, '/register')
api.add_resource(Classify, '/classify')
api.add_resource(Refill, '/refill')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
