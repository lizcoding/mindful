# Mindful Database
"""Models for movie ratings app."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """A user."""
    
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

    # items = a list of Item objects
    # plans = a list of Plan objects

    def __repr__(self):
        return f"<User user_id={self.user_id} email={self.email}>"


class Retailer(db.Model):
    """A movie rating."""
    
    __tablename__ = 'retailers'

    retailer_id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    # items = a list of Item objects

    def __repr__(self):
        return f"<>"


class Item(db.Model):
    """A tracked item."""
    
    __tablename__ = 'items'

    item_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    retailer_id = db.Column(db.Integer, db.ForeignKey("retailers.retailer_id"))
    # images = a list of Image objects
    # sentiments = a list of Sentiment objects
    # descriptors = a list of Descriptor objects

    user = db.relationship("User", backref="items")
    plan = db.relationship("Plan", backref="items")
    retailer = db.relationship("Retailer", backref="items")

    def __repr__(self):
        return f"<>"


class Plan(db.Model):
    """An item's plan data."""
    
    __tablename__ = 'plans'

    plan_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"))

    # items = a list of Item objects

    user = db.relationship("User", backref="plans")
    
    def __repr__(self):
        return f"<>"


class Image(db.Model):
    """An item image."""
    
    __tablename__ = 'images'

    img_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"))
    
    item = db.relationship("Item", backref="images")

    def __repr__(self):
        return f"<>"


class Sentiment(db.Model):
    """User's sentiment for an item."""
    
    __tablename__ = 'sentiments'

    sentiment_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"))

    item = db.relationship("Item", backref="sentiments")
    
    def __repr__(self):
        return f"<>"


class Descriptor(db.Model):
    """A collection of item data."""
    
    __tablename__ = 'descriptors'

    descriptor_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey("retailers.retailer_id"))
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"))

    item = db.relationship("Item", backref="descriptors")
    
    def __repr__(self):
        return f"<>"


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
