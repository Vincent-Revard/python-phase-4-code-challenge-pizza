#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request
from flask_restful import Api, Resource
from sqlalchemy.orm import joinedload
from sqlalchemy import select
import os
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, NotFound

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.errorhandler(SQLAlchemyError)
def handle_database_error(error):
    return {"error": "Database error: " + str(error)}, 500


@app.errorhandler(BadRequest)
def handle_bad_request(error):
    return {"error": "Bad request: " + str(error)}, 400


@app.errorhandler(NotFound)
def handle_not_found(error):
    return {"error": "Not found: " + str(error)}, 404

#! helpers
def get_all(model, only=None):
    instances = db.session.execute(select(model)).scalars().all()
    if only is None:
        return [instance.to_ordered_dict() for instance in instances]
    else:
        return [instance.to_dict(only=only) for instance in instances]

def get_instance_by_id(model, id):
    if (instance := db.session.get(model, id)) is None:
        raise NotFound(description=f"{model.__name__} not found")
    return instance

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# Base class for CRUD resource classes
class BaseResource(Resource):
    model = None
    fields = None

    def get(self, id=None):
        try:
            if id is None:
                return get_all(self.model, self.fields), 200
            else:
                instance = get_instance_by_id(self.model, id)
                return instance.to_dict(), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"errors": str(e)}, 500

    def delete(self, id):
        instance = get_instance_by_id(self.model, id)
        db.session.delete(instance)
        db.session.commit()
        return "", 204
    
    def post(self):
        raise NotImplementedError("This method must be overridden.")

    def patch(self, id):
        raise NotImplementedError("This method must be overridden.")

class Restaurants(BaseResource):
    model = Restaurant
    fields = ("address", "id", "name")

class Pizzas(BaseResource):
    model = Pizza
    fields = ("ingredients", "id", "name")

class RestaurantPizzas(BaseResource):
    model = RestaurantPizza
    fields = ("id", "price", "restaurant", "pizza")

    def post(self):
        data = request.json
        required_fields = ["restaurant_id", "pizza_id", "price"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {"errors": f"Missing required fields: {', '.join(missing_fields)}"}, 400
        try:
            new_respizza = RestaurantPizza(**data)
            db.session.add(new_respizza)
            db.session.commit()
            return new_respizza.to_dict(), 201
        # except ValueError as e:
        #     db.session.rollback()
        #     return {"errors": str(e)}, 422
        # except TypeError as e:
        #     db.session.rollback()
        #     return {"errors": str(e)}, 422
        # except SQLAlchemyError as e:
        #     db.session.rollback()
        #     return {"errors": str(e)}, 500
        # except Exception as e:
        #     db.session.rollback()
        #     return {"errors": str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400
        #! uncomment 114-119 and comment 120-122 +
        #! follow comment instructions under def test_400_for_validation_error(self):
        #! that is within app_test.py line 183/194 + comment 195-197

    def patch(self, id):
        data = request.json
        required_fields = ["price"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {"errors": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        try:
            respizza = get_instance_by_id(RestaurantPizza, id)

            # If restaurant_id or pizza_id are not in the request data, use the current values
            data.setdefault('restaurant_id', respizza.restaurant_id)
            data.setdefault('pizza_id', respizza.pizza_id)

            for field, value in data.items():
                if hasattr(respizza, field):
                    setattr(respizza, field, value)

            db.session.commit()
            return (
                respizza.to_dict(
                    only=("id", "price", "restaurant", "pizza")
                ),
                200,
            )
        except ValueError as e:
            db.session.rollback()
            return {"errors": str(e)}, 400
        except TypeError as e:
            db.session.rollback()
            return {"errors": str(e)}, 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"errors": str(e)}, 500
        except Exception as e:
            db.session.rollback()
            return {"errors": str(e)}, 400


api.add_resource(Pizzas, "/pizzas")
api.add_resource(Restaurants, "/restaurants", "/restaurants/<int:id>")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas", "/restaurant_pizzas/<int:id>")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
