"""CRUD operations."""

# from flask.templating import _default_template_ctx_processor
# from flask_sqlalchemy import _record_queries
from model import db, User, connect_to_db


def create_user(email, password):
    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()
    
    return user


def get_users():
    return User.query.all()


def get_user_by_id(user_id):
    return User.query.get(user_id)
    

def get_user_by_email(email):
    return User.query.filter(User.email == email).first()


if __name__ == '__main__':
    from server import app
    connect_to_db(app)