# Mindful Database
"""Models Mindful App"""

from email.policy import default
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, user_accessed
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """A user."""
    
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(20), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128))
    phone_number = db.Column(db.String(12))
    # items = a list of Item objects
    # plans = a list of Plan objects
    # calendar = a list of one Calendar object

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} email={self.email} first_name={self.first_name}>"


class Retailer(db.Model):
    """An online retailer."""
    
    __tablename__ = 'retailers'

    retailer_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    returns_url = db.Column(db.String(200), nullable=False)
    # items = a list of Item objects

    def __repr__(self):
        return f"<Retailer retailer_id={self.retailer_id} name={self.name}>"


class Calendar(db.Model):
    """A user's Mindful calendar."""
    __tablename__ = 'calendars'

    calendar_id = db.Column(db.String(200), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False)
    # items = a list of Item objects

    user = db.relationship("User", backref="calendar")

    def __repr__(self):
        return f"<Calendar calendar_id={self.calendar_id} user_id={self.user_id}>"


class Item(db.Model):
    """A tracked item."""
    
    __tablename__ = 'items'

    item_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False)
    retailer_id = db.Column(db.Integer, db.ForeignKey("retailers.retailer_id"), nullable=False)
    calendar_id = db.Column(db.String(200), db.ForeignKey("calendars.calendar_id"))
    event_id = db.Column(db.String(200))
    return_deadline = db.Column(db.Date, nullable=False)
    return_type = db.Column(db.String(10))
    text_reminder = db.Column(db.Boolean, default=False)
    email_reminder = db.Column(db.Boolean, default=False)
    decision_status = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    brand = db.Column(db.String(30))
    # images = a list of Image objects
    # sentiments = a list of Sentiment objects

    calendar = db.relationship("Calendar", backref="items")
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
    action = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    deadline = db.Column(db.Date)
    # items = a list of Item objects

    def __repr__(self):
        return f"<Plan plan_id={self.plan_id} item_id={self.item_id} action={self.action} status={self.status}>"


class Image(db.Model):
    """An item image."""
    
    __tablename__ = 'images'

    img_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"), nullable=False)
    cloudinary_url = db.Column(db.String(200))
    
    item = db.relationship("Item", backref="images")

    def __repr__(self):
        return f"<Image img_id={self.img_id} item_id={self.item_id} cloudinary_url={self.cloudinary_url}>"


class Sentiment(db.Model):
    """A user's sentiment entry for an item."""
    
    __tablename__ = 'sentiments'

    sentiment_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.item_id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    entry = db.Column(db.String(500), nullable=False)
    general_sentiment_label = db.Column(db.String(20), nullable=False)
    general_sentiment_score = db.Column(db.Numeric, nullable=False)
    
    # document level emotion result is stored in Sentiment
    sadness = db.Column(db.Numeric, default=None)
    joy = db.Column(db.Numeric, default=None)
    fear = db.Column(db.Numeric, default=None)
    disgust = db.Column(db.Numeric, default=None)
    anger = db.Column(db.Numeric, default=None)

    item = db.relationship("Item", backref="sentiments")
    entities = db.relationship("Entity", backref="sentiment")
    keywords = db.relationship("Keyword", backref="sentiment")
    targets = db.relationship("Target", backref="sentiment")
    
    def __repr__(self):
        return f"<Sentiment sentiment_id={self.sentiment_id} item_id={self.item_id} date={self.date} overall_score={self.general_sentiment_score} overall_sentiment_label={self.general_sentiment_label}>"


class Entity(db.Model):
    """An entity returned through a sentiment analysis of a reflection entry."""
    
    __tablename__ = 'entities'
    
    entity_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    sentiment_id = db.Column(db.Integer, db.ForeignKey("sentiments.sentiment_id"), nullable=False)
    entity_type = db.Column(db.String(100))
    text = db.Column(db.String(100), nullable=False)
    sentiment_score = db.Column(db.Numeric, nullable=False)
    sentiment_label = db.Column(db.String(20), nullable=False)
    relevance = db.Column(db.Numeric, nullable=False)
    # sentiment = a list of one Sentiment object
    
    # emotion
    sadness = db.Column(db.Numeric, default=None)
    joy = db.Column(db.Numeric, default=None)
    fear = db.Column(db.Numeric, default=None)
    disgust = db.Column(db.Numeric, default=None)
    anger = db.Column(db.Numeric, default=None)

    def __repr__(self):
        return f"<Entity entity_id={self.entity_id} sentiment_id={self.sentiment_id} entity_type={self.entity_type} text={self.text} sentiment_score={self.sentiment_score} sentiment_label={self.sentiment_label} relevance={self.relevance}>"


class Keyword(db.Model):
    """A keyword (dynamically generated)returned through a sentiment analysis of a reflection entry."""
    
    __tablename__ = 'keywords'
    
    keyword_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    sentiment_id = db.Column(db.Integer, db.ForeignKey("sentiments.sentiment_id"), nullable=False)
    text = db.Column(db.String(20), nullable=False)
    sentiment_score = db.Column(db.Numeric, nullable=False)
    relevance = db.Column(db.Numeric, nullable=False)
    # sentiment = a list of one Sentiment object
    
    # emotion 
    sadness = db.Column(db.Numeric, default=None)
    joy = db.Column(db.Numeric, default=None)
    fear = db.Column(db.Numeric, default=None)
    disgust = db.Column(db.Numeric, default=None)
    anger = db.Column(db.Numeric, default=None)
    
    def __repr__(self):
        return f"<Keyword keyword_id={self.keyword_id} sentiment_id={self.sentiment_id} text={self.text} sentiment_score={self.sentiment_score} relevance={self.relevance}>"


class Target(db.Model):
    """A target (hard-coded keyword) returned through a sentiment analysis of a reflection entry."""
    
    __tablename__ = 'targets'
    
    target_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    sentiment_id = db.Column(db.Integer, db.ForeignKey("sentiments.sentiment_id"), nullable=False)
    text = db.Column(db.String(20), nullable=False)
    sentiment_score = db.Column(db.Numeric, nullable=False)
    sentiment_label = db.Column(db.String(20), nullable=False)
    # sentiment = a list of one Sentiment object

    # emotion 
    sadness = db.Column(db.Numeric, default=None)
    joy = db.Column(db.Numeric, default=None)
    fear = db.Column(db.Numeric, default=None)
    disgust = db.Column(db.Numeric, default=None)
    anger = db.Column(db.Numeric, default=None)
    
    def __repr__(self):
        return f"<Target target_id={self.target_id} sentiment_id={self.sentiment_id} text={self.text} sentiment_score={self.sentiment_score} sentiment_label={self.sentiment_label}>"


def connect_to_db(flask_app, db_uri="postgresql:///mindful", echo=True):
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
