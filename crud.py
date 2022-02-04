"""CRUD operations."""

# from flask.templating import _default_template_ctx_processor
# from flask_sqlalchemy import _record_queries
from sqlalchemy import ForeignKey
from sqlalchemy.sql.elements import TextClause
from model import Calendar, db, User, Retailer, Item, Plan, Image, Sentiment, Entity, Target, Keyword, connect_to_db


# User object CRUD functions
def create_user(email, password, first_name):
    user = User(id=email, email=email, first_name=first_name)
    db.session.add(user)
    user.set_password(password)
    db.session.commit()
    return user

def set_phone_number(user, phone_number):
    user.phone_number = phone_number
    db.session.commit()

def remove_phone_number(user):
    user.phone_number = None
    db.session.commit()
    
def verify_user(user):
    user.verified = True
    db.session.commit()

def get_users():
    return User.query.all()

def get_user_by_id(user_id):
    return User.query.get(user_id)
    
def get_user_by_email(email):
    return User.query.filter(User.email == email).first()


# Calendar object CRUD functions
def create_calendar(user, calendar_id):
    calendar = Calendar(calendar_id=calendar_id, user_id=user.id)
    db.session.add(calendar)
    db.session.commit()
    return calendar

def add_calendar_item(item, calendar):
    item.calendar_id = calendar.calendar_id
    db.session.commit()


# Retailer object CRUD functions
def create_retailer(name, returns_url):
    retailer = Retailer(name=name, returns_url=returns_url)
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
def create_item(user_id, retailer_id, brand, price, return_deadline, return_type):
    item = Item(user_id=user_id, retailer_id=retailer_id, brand=brand, price=price,
        return_deadline=return_deadline, return_type=return_type, decision_status="Undecided")
    db.session.add(item)
    db.session.commit()
    return item

def get_item_by_id(item_id):
    return Item.query.get(item_id)

def delete_item(item):
    remove_plan(item)
    delete_images(item)
    delete_sentiments(item)
    db.session.delete(item)
    db.session.commit()

def delete_images(item):
    if item.images:
        for img in item.images:
            db.session.delete(img)
    db.session.commit()

def delete_sentiments(item):
    for sentiment in item.sentiments:
        delete_keywords(sentiment)
        delete_targets(sentiment)    
        delete_entities(sentiment)        
        db.session.delete(sentiment)
    db.session.commit()

def delete_keywords(sentiment):
    if sentiment.keywords:
        for keyword in sentiment.keywords:
            db.session.delete(keyword)

def delete_targets(sentiment):
    if sentiment.targets:
        for target in sentiment.targets:
            db.session.delete(target)

def delete_entities(sentiment):
    if sentiment.entities:
        for entity in sentiment.entities:
            db.session.delete(entity)

def set_item_reminders(item, text, email):
    if text:
        item.text_reminders = True
    if email:
        item.email_reminders = True
    db.session.commit()

def set_item_status(item, status):
    item.decision_status = status
    db.session.commit()

# Plan object CRUD functions
def create_plan(item, action):
    plan = Plan(item_id=item.item_id, action=action, status="In Progress")
    item.decision_status = "In-Progess"
    db.session.add(plan)
    
    if action == "Return":
        plan.deadline = item.return_deadline
    
    db.session.commit()
    return plan

def get_plan_by_id(plan_id):
    return Plan.query.get(plan_id)

def remove_plan(item):
    if item.plan:
        db.session.delete(item.plan[0])
        item.decision_status = "Undecided"
    db.session.commit()

def complete_plan(item, plan):
    plan.status = "Complete"
    item.decision_status = "Complete"
    db.session.commit()


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


# set emotion attributes
def set_emotions(object, emotion_list):
        object.sadness = emotion_list["sadness"]
        object.joy = emotion_list["joy"]
        object.fear = emotion_list["fear"]
        object.disgust = emotion_list["disgust"]
        object.anger = emotion_list["anger"]
        db.session.commit()

def create_entity(sentiment, result):
    entity = Entity(
            sentiment_id=sentiment.sentiment_id, 
            entity_type=result["type"],
            text=result["text"], 
            sentiment_score=result["sentiment"]["score"],
            sentiment_label=result["sentiment"]["label"], 
            relevance=result["relevance"]
        )
    db.session.add(entity)
    db.session.commit()
    return entity

def create_keyword(sentiment, result):
    keyword = Keyword(
        sentiment_id=sentiment.sentiment_id, 
        text=result["text"], 
        sentiment_score=result["sentiment"]["score"],
        relevance=result["relevance"]
    )
    db.session.add(keyword)
    db.session.commit()
    return keyword

def create_target(sentiment, sentiment_result):
    target = Target(
        sentiment_id=sentiment.sentiment_id,
        text=sentiment_result["text"], 
        sentiment_score=sentiment_result["score"],
        sentiment_label=sentiment_result["label"]
    )
    db.session.add(target)
    db.session.commit()
    return target

# Sentiment object CRUD functions
def create_sentiment(item_id, date, entry, general_sentiment_score, general_sentiment_label):
    sentiment = Sentiment(
        item_id=item_id, date=date, entry=entry,
        general_sentiment_score=general_sentiment_score, 
        general_sentiment_label=general_sentiment_label)

    db.session.add(sentiment)
    db.session.commit()
    return sentiment


def get_sentiment_by_id(sentiment_id):
    return Sentiment.query.get(sentiment_id)


if __name__ == '__main__':
    from server import app
    connect_to_db(app)