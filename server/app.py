#!/usr/bin/env python3

from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
import os

# Import models
from models import db, Restaurant, RestaurantPizza, Pizza

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        response_dict_list = [restaurant.to_dict(rules=('-restaurant_pizzas',)) for restaurant in Restaurant.query.all()]
        return make_response(jsonify(response_dict_list), 200)

class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant:
            return make_response(jsonify(restaurant.to_dict(rules=('restaurant_pizzas',))), 200)
        return make_response(jsonify({"error": "Restaurant not found"}), 404)

    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            return make_response(jsonify({"message": "record successfully deleted"}), 204)
        return make_response(jsonify({"error": "Restaurant not found"}), 404)

class Pizzas(Resource):
    def get(self):
        response_dict_list = [pizza.to_dict(rules=('-restaurant_pizzas',)) for pizza in Pizza.query.all()]
        return make_response(jsonify(response_dict_list), 200)

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        try:
            if data["price"] < 1 or data["price"] > 30:
                raise ValueError("Price must be between 1 and 30")

            new_record = RestaurantPizza(
                price=data["price"],
                restaurant_id=data["restaurant_id"],
                pizza_id=data["pizza_id"]
            )

            db.session.add(new_record)
            db.session.commit()
            
            response = new_record.to_dict()
            response['pizza'] = new_record.pizza.to_dict(only=('id', 'name', 'ingredients'))
            response['restaurant'] = new_record.restaurant.to_dict(only=('id', 'name', 'address'))
            
            return make_response(jsonify(response), 201)
        except ValueError as e:
            return make_response(jsonify({"errors": ["validation errors"]}), 400)
        except Exception as e:
            return make_response(jsonify({"errors": [str(e)]}), 400)

api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantByID, "/restaurants/<int:id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
