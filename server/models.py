from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, select
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)


class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)

    # add relationship
    restaurant_pizzas = db.relationship(
        "RestaurantPizza", back_populates="restaurant", cascade="all, delete-orphan"
    )
    pizzas = association_proxy("restaurant_pizzas", "pizza")
    # add serialization rules
    serialize_rules = ("-restaurant_pizzas.restaurant",)

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ingredients = db.Column(db.String)

    # add relationship
    restaurant_pizzas = db.relationship(
        "RestaurantPizza", back_populates="pizza", cascade="all, delete-orphan"
    )
    pizzas = association_proxy("restaurant_pizzas", "restaurant")
    # add serialization rules
    serialize_rules = ("-restaurant_pizzas.pizza",)

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"


class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurants.id"), nullable=False
    )
    pizza_id = db.Column(db.Integer, db.ForeignKey("pizzas.id"), nullable=False)
    # add relationships
    restaurant = db.relationship("Restaurant", back_populates="restaurant_pizzas")
    pizza = db.relationship("Pizza", back_populates="restaurant_pizzas")
    # add serialization rules
    serialize_rules = ("-restaurant.restaurant_pizzas", "-pizza.restaurant_pizzas")

    # def to_ordered_dict(self):
    #     data = self.to_dict()
    #     return {key: data[key] for key in ("id", "restaurant", "pizza", "price")}

    def to_ordered_dict(self):
        data = self.to_dict()
        ordered_data = {
            "id": data["id"],
            "restaurant": {"name": data["restaurant"]["name"]},
            "pizza": {"name": data["pizza"]["name"]},
            "price": data["price"]
        }
        return ordered_data

    # add validation
    # @validates("price")
    # def validate_price(self, _, price):
    #     if not isinstance(price, int):
    #         raise TypeError("Price must be an integer")
    #     if not (1 <= price <= 30):
    #         raise ValueError("Price must be in between 1 and 30")
    #     return price

    @validates("restaurant_id", "pizza_id", "price")
    def validate_ids(self, key, value):
        if key in ["restaurant_id", "pizza_id"]:
            if not isinstance(value, int):
                raise TypeError("ID must be an integer")

            # Check if the Restaurant or Pizza exist in the instance
            if key == "restaurant_id":
                model = Restaurant
            elif key == "pizza_id":
                model = Pizza

            if (
                db.session.execute(
                    select(model).where(model.id == value)
                ).scalar_one_or_none()
                is None
            ):
                raise ValueError(f"{model.__name__} not found")
        elif key == "price":
            if not isinstance(value, (int, float)):
                raise TypeError("Price must be an integer")
            if not (1 <= value <= 30):
                raise ValueError("Price must be between 1 and 30")

        return value

    def __repr__(self):
        return f"<RestaurantPizza restaurant={self.restaurant.name}, pizza={self.pizza.name}, price=${self.price}>"
