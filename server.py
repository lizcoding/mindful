from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EmotionOptions, EntitiesOptions, KeywordsOptions, SentimentOptions
from flask import (Flask, redirect, flash, request, render_template, session)
from jinja2 import StrictUndefined
from markupsafe import re
from model import connect_to_db
import cloudinary.uploader
import datetime
import crud
import json
import os

# <------- UP NEXT ---------------------------------------------------------------->
# [ ] Make sure emotions are working (put in Item HTML)

# <------- TO-DO's: Odds and Ends -------------------------------------------------->
# [ ] Validate Add Item Form (can't add dates in the past)
# [ ] Automatically calculate return deadline date

# [ ] Change "Status" when plan has been added + when plan has been executed
# [ ] Remove "Add Details", "Add Plan" forms for items with existing details/plans

# [ ] Create Profile route for non-tracked items (items that finished Mindful track-plan life-cycle)
# [ ] Order items/plans on dashboard by time-sensitivity (Days left)
# [ ] Show top 3 items OR plans at the very top of the page

# <------- END OF MVP - On the Horizon ---------------------------------------------->
# END OF MVP: IMB Watson integration up and running
#
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
    # Make sure tracked items are ordered by return_deadline
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


@app.route("/item/<item_id>/add_sentiment", methods=['POST'])
def add_sentiment(item_id):
    if not session.get("user_id"):
        return redirect("/")
    date = session["today"]
    item = crud.get_item_by_id(item_id)
    previous_sentiments = item.sentiments
    today_list =[int(num) for num in date.split('-')]
    today = datetime.date(today_list[0], today_list[1], today_list[2])
    
    # if previous_sentiments:
    #     for record in previous_sentiments[::]:
    #         if record.date == today:
    #             flash("Today's reflection has already been entered!")
    #             return redirect(f"/item/{item_id}")
    
    
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
        item_id, date, entry, general_sentiment_score, general_sentiment_label)
    crud.set_emotions(sentiment, document_emotions)

    if entities:
        for result in entities:
            entity = crud.create_entity(sentiment, result)
            # sentiment.entities.append(entity)
            crud.set_emotions(entity, result["emotion"])
            
    if keywords:
        for result in keywords:
            keyword = crud.create_keyword(sentiment, result)
            # sentiment.keywords.append(keyword)
            crud.set_emotions(keyword, result["emotion"])
    
    if sentiment_targets and emotion_targets:
        for sentiment_result, emotion_result in zip(sentiment_targets, emotion_targets):
            target = crud.create_target(sentiment, sentiment_result)
            # sentiment.targets.append(target)
            crud.set_emotions(target, emotion_result["emotion"])

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
