"""CRUD operations."""

# from flask.templating import _default_template_ctx_processor
# from flask_sqlalchemy import _record_queries
from sqlalchemy.sql.elements import TextClause
from model import db, User, Retailer, Item, Plan, Image, Sentiment, connect_to_db


# User object CRUD functions
def create_user(email, password, first_name):
    user = User(email=email, password=password, first_name=first_name)
    db.session.add(user)
    db.session.commit()
    return user

def get_users():
    return User.query.all()

def get_user_by_id(user_id):
    return User.query.get(user_id)
    
def get_user_by_email(email):
    return User.query.filter(User.email == email).first()


# Retailer object CRUD functions
def create_retailer(name, main_url, returns_url, return_window):
    retailer = Retailer(name=name, main_url=main_url, returns_url=returns_url, return_window=return_window)
    db.session.add(retailer)
    db.session.commit()
    return retailer

def get_retailer_by_id(retailer_id):
    return Retailer.query.get(retailer_id)

def get_retailer_by_name(user, name):
    items = user.items
    retailers = [item.retailer.name.lower() for item in items]
    if name.lower() in retailers:
        return Retailer.query.filter(Retailer.name.ilike(name), Retailer.retailer_id.in_([item.retailer_id for item in items])).first()
    else:
        return False

# Item object CRUD functions
def create_item(user_id, retailer_id, item_url):
    item = Item(user_id=user_id, retailer_id=retailer_id, item_url=item_url, decision_status="Undecided")
    db.session.add(item)
    db.session.commit()
    return item

def get_item_by_id(item_id):
    return Item.query.get(item_id)

def set_item_reminders(item, text, email):
    if text:
        item.text_reminders = True
    else:
        item.text_reminders = False
    if email:
        item.email_reminders = True
    else:
        item.email_reminders = False
    db.session.commit()

def set_item_details(item, materials, size, care):
    if materials:
        item.materials = materials
    if size:
        item.size = size
    if care:
        item.care = care
    db.session.commit()

# def get_undecided_items(user_id):
#     return Item.query.filter((Item.user_id == user_id) and (Item.decision_status == "Undecided")).all()


# Plan object CRUD functions
def create_plan(item_id, action):
    plan = Plan(item_id=item_id, action=action, status="In Progress")
    db.session.add(plan)
    db.session.commit()
    return plan

def get_plan_by_id(plan_id):
    return Plan.query.get(plan_id)


# Image object CRUD functions
def create_image(item):
    img = Image()
    item.images.append(img)
    db.session.commit()
    return img

def add_image_url(image, url):
    image.cloudinary_url = url
    db.session.commit()

def get_image_by_id(img_id):
    return Image.query.get(img_id)


# Sentiment object CRUD functions
def create_sentiment(item_id, text_entry, analysis, score):
    sentiment = Sentiment(item_id=item_id, text_entry=text_entry, analysis=analysis, score=score)
    db.session.add(sentiment)
    db.session.commit()
    return sentiment

def get_sentiment_by_id(sentiment_id):
    return Sentiment.query.get(sentiment_id)


if __name__ == '__main__':
    from server import app
    connect_to_db(app)