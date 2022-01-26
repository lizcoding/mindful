from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EmotionOptions, EntitiesOptions, KeywordsOptions, SentimentOptions
from flask import (Flask, redirect, flash, request, render_template, session)
from jinja2 import StrictUndefined
from model import connect_to_db
from google.oauth2 import id_token
from google.auth.transport import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient
# from markupsafe import re
import functools
import random
import string
import flask_login
import cloudinary.uploader
import datetime
import crud
import json
import os

# <------- UP NEXT ----------------------------------------------------------------->
# [ ] Add more features to Flask Login: https://flask-login.readthedocs.io/en/latest/#flask_login.login_required
# [ ] Keep One: return deadline or return window
# [ ] Add display logic (make reccomendation) for sentiment analysis data

# <------- TO-DO's: Odds and Ends -------------------------------------------------->
# [ ] Show top 3 items OR plans at the very top of the page
# [ ] Modify "Add Details" text for items with existing details
# [ ] Build out Plans (focus on non-return actions)

# <------- END OF MVP - On the Horizon ---------------------------------------------->
# END OF MVP: Cloudinary API, Google Maps API, IBM NLU API integration. Flask login and Google OAuth.
# All database objects have functional + robust CRUD and HTML displays logically  
# TO-DO: Review code and refactor/modularize where appropriate. Ask for a code review.

# <------- SPRINT 2: General Plans -------------------------------------------------->
# Testing
# User Experience
# Autocomplete for retailers and autofill fields
# Some Design

# <------- EXTRAS ------------------------------------------------------------------->
# Try to get Joe to break my site :)
# Ask Anjelica to rate features for automation


app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.filters['zip'] = zip

# Required to use Flask sessions
app.secret_key = os.environ['MINDFUL_KEY']

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/"

# Configure Cloudinary API
CLOUD_NAME = os.environ['CLOUD_NAME']
CLOUDINARY_KEY = os.environ['CLOUD_KEY']
CLOUDINARY_SECRET = os.environ['CLOUD_SECRET']

# Configure IBM Natural Language Understanding
authenticator = IAMAuthenticator(os.environ['IBM_NATURAL_LANGUAGE_KEY'])
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2021-08-01',
    authenticator=authenticator
)
natural_language_understanding.set_service_url(os.environ['IBM_NATURAL_LANGUAGE_URL'])

# Configure Google OAuth
CLIENT_ID = os.environ["client_id"]
# LOGIN_SCOPES = ['https://www.googleapis.com/openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
# CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
# API_SERVICE_NAME = 'openid'
# API_VERSION = 'v2'




def get_random_string():
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(20))
    return result_str


@login_manager.user_loader
def load_user(user_id):
    return crud.get_user_by_id(user_id)


@app.context_processor
def inject_client_id():
    return dict(client_id=CLIENT_ID)


@app.route("/")
def login_page():
    if not flask_login.current_user.is_authenticated:
        return render_template("login.html")
    else:
        return redirect("/dashboard")


@app.route("/tokensignin", methods=['GET', 'POST'])
def verify_token():
    token = request.form.get('credential')

    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        
        if not crud.get_user_by_email(idinfo['email']):
            password = get_random_string()
            user = crud.create_user(email=idinfo['email'], password=password, first_name=idinfo['given_name'])
        else:
            user = crud.get_user_by_email(idinfo['email'])
        
        today = datetime.date.today().isoformat()
        session["today"] = today
        flask_login.login_user(user)
        return redirect("/dashboard")
    
    except ValueError:
        # Invalid token
        print("ValueError")
        return redirect("/")


@app.route("/create_account", methods=["POST"])
def register_user():
    email = request.form.get("email")
    user = crud.get_user_by_email(email)

    if user:
        flash("That email is already associated with an account.")
    else:
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        crud.create_user(email, password, first_name)
        flash("Account created!")
      
    return redirect("/")


@app.route("/login", methods=['GET', 'POST'])
def handle_login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = crud.get_user_by_email(email)

    if user:
        if user.email == email and user.check_password(password):
            today = datetime.date.today().isoformat()
            session["today"] = today
            flask_login.login_user(user)
            return redirect("/dashboard")
    else:
        flash("Invalid login credentials.")
        return redirect("/")


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect("/")


@app.route("/dashboard")
@flask_login.login_required
def dashboard():
    user = flask_login.current_user
    # Make sure tracked items are ordered by return_deadline
    tracked_items = [item for item in user.items if item.decision_status != "Complete"]
    tracked_items.sort(key=lambda x: x.return_deadline)
    
    plans = [item.plan for item in tracked_items if item.plan and item.decision_status != "Complete"]
    
    today = datetime.date.fromisoformat(session["today"])
    deltas = []
    for item in tracked_items:
        return_deadline = item.return_deadline
        delta = return_deadline - today
        deltas.append(delta)
    
    return render_template("dashboard.html", user=user, tracked_items=tracked_items, plans=plans, today=today, deltas=deltas)


# For viewing user's historical data
@app.route("/profile")
@flask_login.login_required
def show_profile():
    user = crud.get_user_by_id(flask_login.current_user.id)
    completed_items = [item for item in user.items if item.decision_status == "Complete"]
    # TO-DO
    return render_template("profile.html", user=user, completed_items=completed_items)


@app.route("/item/<item_id>")
@flask_login.login_required
def item_details(item_id):
    item = crud.get_item_by_id(item_id)
    today = datetime.date.fromisoformat(session["today"])
    days_left = item.return_deadline - today
    all_scores = [sentiment.general_sentiment_score for sentiment in item.sentiments]
    if all_scores: 
        overall_score = functools.reduce(lambda a, b: a + b, all_scores)
    else:
        overall_score = None
    return render_template("item.html", item=item, today=today, days_left=days_left, overall_score=overall_score)


@app.route("/add_item", methods=['POST'])
@flask_login.login_required
def add_item():
    user = crud.get_user_by_id(flask_login.current_user.id)
    item_url = request.form.get("item_url")
    return_deadline = request.form.get("return_deadline")
    return_type = request.form.get("return_type")
    brand = request.form.get("brand")
    retailer_name = request.form.get("retailer")
    price = request.form.get("price")

    if not crud.get_retailer_by_name(user, retailer_name):
        main_url = request.form.get("main_url")
        returns_url = request.form.get("returns_url")
        return_window = request.form.get("return_window")
        if return_window:
            return_window = int(return_window)
        retailer = crud.create_retailer(name=retailer_name, main_url=main_url, returns_url=returns_url, return_window=return_window)
    else:
        retailer = crud.get_retailer_by_name(user, retailer_name)
    
    item = crud.create_item(user.id, retailer.retailer_id, brand, item_url, price, return_deadline, return_type)
    
    text = request.form.get("text")
    email = request.form.get("email")
    crud.set_item_reminders(item, text, email)

    file = request.files["image"]
    image = crud.create_image(item)
    result = cloudinary.uploader.upload(file, api_key=CLOUDINARY_KEY, api_secret=CLOUDINARY_SECRET, cloud_name=CLOUD_NAME)
    img_url = result['secure_url']
    crud.add_image_url(image, img_url)

    return redirect("/dashboard")


@app.route("/item/<item_id>/add_detail", methods=['POST'])
@flask_login.login_required
def add_detail(item_id):
    cotton = request.form.get("cotton")
    wool = request.form.get("wool")
    leather = request.form.get("leather")
    faux_leather = request.form.get("faux_leather")
    elastane = request.form.get("elastane")
    polyester = request.form.get("polyester")
    acrylic = request.form.get("acrylic")
    viscose = request.form.get("viscose")
    silk = request.form.get("wool")
    cashmere = request.form.get("wool")
    
    form_values = [cotton, wool, leather, faux_leather, elastane,
                    polyester, acrylic, viscose, silk, cashmere]
            
    materials = f'{[material for material in form_values if material]}'
    num_size = request.form.get("int_size")
    str_size = request.form.get("alpha_size")
    if num_size:
        size = num_size
    else:
        size = str_size

    care = request.form.get("care")
    item = crud.get_item_by_id(item_id)
    crud.set_item_details(item, materials, size, care)

    return redirect(f"/item/{item_id}")


@app.route("/item/<item_id>/add_sentiment", methods=['POST'])
@flask_login.login_required
def add_sentiment(item_id):
    item = crud.get_item_by_id(item_id)
    previous_sentiments = item.sentiments
    today = datetime.date.fromisoformat(session["today"])
    
    if previous_sentiments:
        for record in previous_sentiments[::]:
            if record.date == today:
                flash("Today's reflection has already been entered!")
                return redirect(f"/item/{item_id}")
    
    entry = request.form.get("reflection")
    
    response = natural_language_understanding.analyze(text=entry, features=Features(
        entities=EntitiesOptions(emotion=True, sentiment=True, limit=2),
        emotion=EmotionOptions(targets=['item', 'fit', 'size', 'value', 
        'worth', 'keep', 'return', 'quality', 'wear', 'color']),
        keywords=KeywordsOptions(emotion=True, sentiment=True, limit=3),
        sentiment=SentimentOptions(targets=['item', 'fit', 'size', 'value', 
        'worth', 'keep', 'return', 'quality', 'wear', 'color']))).get_result()

    response_dump = json.dumps(response, indent=2)
    print(response_dump)

    if not response.get("emotion"):
        document_emotions = []
    elif not response["emotion"].get("document"):
        document_emotions = []
    else:
        emotion_targets = [target for target in response["emotion"]["targets"]]
        document_emotions = response["emotion"]["document"]["emotion"]

    if not response.get("entities"):
        entities = []
    else:
        entities = [entity for entity in response["entities"]]

    if not response.get("keywords"):
        keywords = []
    else:
        keywords = [keyword for keyword in response["keywords"]]

    if not response.get("sentiment"):
            flash("Unable to generate sentiment analysis from text entered.")
            return redirect(f"/item/{item_id}")
    elif not response["sentiment"].get("targets"):
            sentiment_targets = []
    else:
        sentiment_targets = [target for target in response["sentiment"]["targets"]]
        general_sentiment_score = response["sentiment"]["document"]["score"]
        general_sentiment_label = response["sentiment"]["document"]["label"]
    
    sentiment = crud.create_sentiment(
        item_id, today, entry, general_sentiment_score, general_sentiment_label)
    crud.set_emotions(sentiment, document_emotions)

    if entities:
        for result in entities:
            entity = crud.create_entity(sentiment, result)
            crud.set_emotions(entity, result["emotion"])
            
    if keywords:
        for result in keywords:
            keyword = crud.create_keyword(sentiment, result)
            crud.set_emotions(keyword, result["emotion"])
    
    if sentiment_targets and emotion_targets:
        for sentiment_result, emotion_result in zip(sentiment_targets, emotion_targets):
            target = crud.create_target(sentiment, sentiment_result)
            crud.set_emotions(target, emotion_result["emotion"])

    return redirect(f"/item/{item_id}")


@app.route("/item/<item_id>/add_plan", methods=['POST'])
@flask_login.login_required
def add_plan(item_id):
    item = crud.get_item_by_id(item_id)
    if not item.plan:
        action = request.form.get("action")
        crud.create_plan(item, action=action)
    else:
        flash("This item had a plan in progress.")

    return redirect(f"/plan/{item.plan[0].plan_id}")


@app.route("/item/<item_id>/keep")
@flask_login.login_required
def keep_item(item_id):
    item = crud.get_item_by_id(item_id)
    crud.set_item_status(item, "Complete")

    if item.plan:
        plan = item.plan[0]
        crud.complete_plan(item, plan)

    return redirect(f"/profile")

@app.route("/item/<item_id>/delete")
@flask_login.login_required
def delete_item(item_id):
    
    item = crud.get_item_by_id(item_id)
    crud.delete_item(item)

    return redirect(f"/dashboard")


@app.route("/plan/<plan_id>")
@flask_login.login_required
def plan_details(plan_id):
    plan = crud.get_plan_by_id(plan_id)
    item = crud.get_item_by_id(plan.item_id)
    gmaps_key = os.environ["gmaps_key"]

    return render_template("plan.html", plan=plan, item=item, gmaps_key=gmaps_key)


@app.route("/plan/<plan_id>/remove_plan")
@flask_login.login_required
def remove_plan(plan_id):
    plan = crud.get_plan_by_id(plan_id)
    item = crud.get_item_by_id(plan.item_id)
    crud.remove_plan(item)

    return redirect(f"/item/{item.item_id}")


@app.route("/plan/<plan_id>/complete_plan")
@flask_login.login_required
def complete_plan(plan_id):
    plan = crud.get_plan_by_id(plan_id)
    item = crud.get_item_by_id(plan.item_id)
    crud.complete_plan(item, plan)

    return redirect(f"/profile")


if __name__ == "__main__":
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)
