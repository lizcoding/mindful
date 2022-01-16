from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions, SentimentOptions
from flask import (Flask, redirect, flash, request, render_template, session)
from jinja2 import StrictUndefined
from markupsafe import re
from model import connect_to_db
import cloudinary.uploader
import datetime
import crud
import json
import os

# <----------- UP NEXT ------------------->
# TO-DO: [ ] Edit model.py to add emotion attributes to Entity, Keyword, and Target tables

# <----------- TO-DO's: Odds and Ends ------------------->
# TO-DO: [ ] Validate Add Item Form (can't add dates in the past)
# TO-DO: [ ] Automatically calculate return deadline date

# TO-DO: [ ] Change "Status" when plan has been added + when plan has been executed
# TO-DO: [ ] Remove "Add Details", "Add Plan" forms for items with existing details/plans

# TO-DO: [ ] Create Profile route for non-tracked items (items that finished Mindful track-plan life-cycle)
# TO-DO: [ ] Order items/plans on dashboard by time-sensitivity (Days left)
# TO-DO: [ ] Show top 3 time-sensitive items or plans at the very top of the page

# <----------- END OF MVP - On the Horizon ------------------->
# END OF MVP: IMB Watson integration up and running
# On the horizon: 
#   OAuth login (login with google, sync with Google Calendar)
#   Dynamic search for retailers + items
#   Implement Flask Login (more features): https://flask-login.readthedocs.io/en/latest/#flask_login.login_required
#   Google Search Bar then scrape data? Hidden store parameter
#   Try to get Joe to break my site :)
#   Ask Anjelica to rate features for automation


app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.filters['zip'] = zip

# Required to use Flask sessions
app.secret_key = os.environ['MINDFUL_KEY']

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


@app.route("/")
def login():
    if session.get("user_id"):
        return redirect("/dashboard")
    else:
        return render_template("login.html")


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


@app.route("/login", methods=['POST'])
def handle_login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = crud.get_user_by_email(email)

    if user:
        if user.email == email and user.password == password:
            today = datetime.date.today().isoformat()
            session["today"] = today
            session["user_id"] = user.user_id
            return redirect("/dashboard")
    else:
        flash("Invalid login credentials.")
        return redirect("/")


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/")
    user = crud.get_user_by_id(session["user_id"])
    # Make sure tracked items is ordered by return_deadline
    tracked_items = [item for item in user.items if item.decision_status == "Undecided"]
    plans = [item.plan for item in user.items if item.plan]
    
    today = session.get("today")
    today_list =[int(num) for num in today.split('-')]
    deltas = []
    
    for item in tracked_items:
        return_deadline = item.return_deadline
        delta = return_deadline - datetime.date(today_list[0], today_list[1], today_list[2])
        deltas.append(delta)
    
    return render_template("dashboard.html", user=user, tracked_items=tracked_items, plans=plans, today=today, deltas=deltas)
    

@app.route("/item/<item_id>")
def item_details(item_id):
    if not session.get("user_id"):
        return redirect("/")
    item = crud.get_item_by_id(item_id)
    date = session["today"]
    today_list =[int(num) for num in date.split('-')]
    today = datetime.date(today_list[0], today_list[1], today_list[2])
    days_left = item.return_deadline - today

    return render_template("item.html", item=item, days_left=days_left)


@app.route("/add_item", methods=['POST'])
def add_item():
    if not session.get("user_id"):
        return redirect("/")
    user = crud.get_user_by_id(session["user_id"])
    item_url = request.form.get("item_url")
    return_deadline = request.form.get("return_deadline")
    return_type = request.form.get("return_type")
    brand = request.form.get("brand")
    retailer_name = request.form.get("retailer")
    price = request.form.get("price")

    if not crud.get_retailer_by_name(user, retailer_name):
        main_url = request.form.get("main_url")
        returns_url = request.form.get("returns_url")
        return_window = int(request.form.get("return_window"))
        retailer = crud.create_retailer(name=retailer_name, main_url=main_url, returns_url=returns_url, return_window=return_window)
    else:
        retailer = crud.get_retailer_by_name(user, retailer_name)
    
    item = crud.create_item(user.user_id, retailer.retailer_id, brand, item_url, price, return_deadline, return_type)
    
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
def add_detail(item_id):
    if not session.get("user_id"):
        return redirect("/")
    
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


# DO TODAY (1/14)
@app.route("/item/<item_id>/add_sentiment", methods=['POST'])
def add_sentiment(item_id):
    if not session.get("user_id"):
        return redirect("/")
    date = session["today"]
    item = crud.get_item_by_id(item_id)
    previous_sentiments = item.sentiments
    today_list =[int(num) for num in date.split('-')]
    today = datetime.date(today_list[0], today_list[1], today_list[2])
    
    if previous_sentiments:
        for record in previous_sentiments[::]:
            if record.date == today:
                flash("Today's reflection has already been entered!")
                return redirect(f"/item/{item_id}")
    
    
    entry = request.form.get("reflection")
    
    response = natural_language_understanding.analyze(text=entry, features=Features(
        entities=EntitiesOptions(emotion=True, sentiment=True, limit=2),
        keywords=KeywordsOptions(emotion=True, sentiment=True, limit=3),
        sentiment=SentimentOptions(targets=['item', 'fit', 'size', 'value', 
        'worth', 'keep', 'return', 'quality', 'wear', 'color']))).get_result()

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
    else:
        if not response.get("sentiment").get("targets"):
            target_words = []
        else:
            target_words = [target for target in response["sentiment"]["targets"]]
            general_sentiment_score = response["sentiment"]["document"]["score"]
            general_sentiment_label = response["sentiment"]["document"]["label"]
    
    crud.create_sentiment(
        item_id, date, entry, general_sentiment_score, general_sentiment_label, 
        entities, keywords, target_words)

    return redirect(f"/item/{item_id}")


@app.route("/item/<item_id>/add_plan", methods=['POST'])
def add_plan(item_id):
    if not session.get("user_id"):
        return redirect("/")
    if not crud.get_item_by_id(item_id).plan:
        action = request.form.get("action")
        crud.create_plan(item_id, action=action)
        flash("Plan created!")
    else:
        flash("This item had a plan in progress.")

    return redirect(f"/item/{item_id}")


@app.route("/plan/<plan_id>")
def plan_details(plan_id):
    if not session.get("user_id"):
        return redirect("/")
    plan = crud.get_plan_by_id(plan_id)
    item = crud.get_item_by_id(plan.item_id)

    return render_template("plan.html", plan=plan, item=item)


# For viewing personal information
#
# @app.route("/profile")
# def show_profile():
#     if not session.get("user"):
#         return redirect("/")
#     user = crud.get_user_by_id(session["user_id"])
    
#     # TO-DO

#     return render_template("profile.html")


if __name__ == "__main__":
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)
