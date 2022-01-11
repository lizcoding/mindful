# Mindful Database
"""Models mindful app"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """A user."""
    
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    street = db.Column(db.String(40))
    unit = db.Column(db.String(10))
    city = db.Column(db.String(20))
    state = db.Column(db.String(2))
    zip = db.Column(db.String(5))
    phone_number = db.Column(db.Integer(11))
    # items = a list of Item objects
    # plans = a list of Plan objects

    def __repr__(self):
        return f"<User user_id={self.user_id} email={self.email}>"


class Retailer(db.Model):
    """An online retailer."""
    
    __tablename__ = 'retailers'

    retailer_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    main_url = db.Column(db.String(50), nullable=False)
    returns_url = db.Column(db.String(50), nullable=False)
    return_window = db.Column(db.Integer(2), nullable=False) # number of days until return
    # items = a list of Item objects

    def __repr__(self):
        return f"<Retailer retailer_id={self.retailer_id} name={self.name}>"


class Item(db.Model):
    """A tracked item."""
    
    __tablename__ = 'items'

    item_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    retailer_id = db.Column(db.Integer, db.ForeignKey("retailers.retailer_id"), nullable=False)
    text_reminder = db.Column(db.Boolean)
    email_reminder = db.Column(db.Boolean)
    entry_date = db.Column(db.Date)
    order_date = db.Column(db.Date)
    delivery_date = db.Column(db.Date)
    order_status = db.Column(db.String(10))
    decision_status = db.Column(db.String(10), nullable=False)
    final_sale = db.Column(db.Boolean)
    item_category = db.Column(db.String(10))
    item_type = db.Column(db.String(10))
    brand = db.Column(db.String(30))
    country_sizing = db.Column(db.String(3))
    size = db.Column(db.String(10))
    color = db.Column(db.String(10))
    machine_washable = db.Column(db.Boolean)
    hand_wash = db.Column(db.Boolean)
    dryclean_only = db.Column(db.Boolean)
    materials = db.Column(db.String(50))
    # images = a list of Image objects
    # sentiments = a list of Sentiment objects

    user = db.relationship("User", backref="items")
    plan = db.relationship("Plan", backref="items")
    retailer = db.relationship("Retailer", backref="items")

    def __repr__(self):
        return f"<Item item_id={self.item_id} user_id={self.user_id} retailer_id={self.retailer_id} decision_status={self.decision_status}>"


class Plan(db.Model):
    """An item's plan data."""
    
    __tablename__ = 'plans'

    plan_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    # items = a list of Item objects

    user = db.relationship("User", backref="plans")
    
    def __repr__(self):
        return f"<Plan plan_id={self.plan_id} item_id={self.item_id} action={self.action} status={self.status}>"


class Image(db.Model):
    """An item image."""
    
    __tablename__ = 'images'

    img_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"), nullable=False)
    cloudinary_url = db.Column(db.String(100), nullable=False)
    
    item = db.relationship("Item", backref="images")

    def __repr__(self):
        return f"<Image img_id={self.img_id} item_id={self.item_id} cloudinary_url={self.cloudinary_url}>"


class Sentiment(db.Model):
    """A user's sentiment entry for an item."""
    
    __tablename__ = 'sentiments'

    sentiment_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"), nullable=False)
    text_entry = db.Column(db.String(100), nullable=False)
    analysis = db.Column(db.String(30), nullable=False)
    score = db.Column(db.Integer(2), nullable=False)

    item = db.relationship("Item", backref="sentiments")
    
    def __repr__(self):
        return f"<Sentiment sentiment_id={self.sentiment_id} item_id={self.item_id} score={self.score}>"


def connect_to_db(flask_app, db_uri="postgresql:///ratings", echo=True):
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    flask_app.config["SQLALCHEMY_ECHO"] = echo
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.app = flask_app
    db.init_app(flask_app)

    print("Connected to the db!")


if __name__ == "__main__":
    from server import app

    # Call connect_to_db(app, echo=False) if your program output gets
    # too annoying; this will tell SQLAlchemy not to print out every
    # query it executes.

    connect_to_db(app)
