from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EmotionOptions, EntitiesOptions, KeywordsOptions, SentimentOptions
from flask import (Flask, redirect, flash, url_for, request, render_template, session)
from jinja2 import StrictUndefined
from model import connect_to_db
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from google.oauth2 import id_token
from google.auth.transport import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import functools
import random
import string
import flask_login
import cloudinary.uploader
import datetime
import crud
import os


# <------- FEATURE TO-DO's ------------------------------------------------------------------------>
# [X] FINISH SENDGRID ROUTE
# [X] Refactor add reflection route

# [ ] IMPORTANT !!!
    # [ ] Make sure Calendar Route checks Calendar Object for items with deadlines in the past, and removes them from calendar.items
    # [X] When deleting an item or completing a plan, update Calendar table accordingly

# [0] Flask Remember Me
# [0] Flask Password Recovery
# [0] Testing
# [ ] Prioritize Store Donation Locations over Donation Drop-Off Boxes for Donation Plan Maps API Result

# <------- BEYOND HACKBRIGHT ----------------------------------------------------------------------->
# [ ] Webscrape Add Item data from Item url
# [ ] Implement Password match for account creation
# [ ] Enable show password toggle for Login/Signup
# [ ] Show app usage data on profile page
# [ ] Allow user to view past Reflection entries


app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.filters['zip'] = zip

# Required to use Flask sessions
app.secret_key = os.environ['MINDFUL_KEY']

# Configure Flask Login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/"

# Configure Twilio APIs
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
VERIFY_SERVICE_SID = os.environ['VERIFY_SERVICE_SID']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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

# Configure Google Calendar OAuth
CLIENT_ID = os.environ["client_id"]
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = os.environ['client_secrets_file']


def get_random_string():
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(20))
    return result_str


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}


def start_verification(to, channel='sms'):
    if channel not in ('sms', 'call'):
        channel = 'sms'

    verification = client.verify \
        .services(VERIFY_SERVICE_SID) \
        .verifications \
        .create(to=to, channel=channel)
    
    return verification.sid


def check_verification(phone, code):
    user_id = session.get("user_id")
    user = crud.get_user_by_id(user_id)
    
    try:
        verification_check = client.verify \
            .services(VERIFY_SERVICE_SID) \
            .verification_checks \
            .create(to=phone, code=code)

        if verification_check.status == "approved":
            crud.verify_user(user)
            if user.phone_number:
                crud.remove_phone_number(user)

            flask_login.login_user(user)
            flash('Your phone number has been verified! Welcome to Mindful.', 'alert-success')
            return redirect("/dashboard")
        else:
            flash('The code you provided is incorrect. Please try again.', 'alert-danger')
    except Exception as e:
        flash("Error validating code: {}".format(e), 'alert-danger')

    return redirect("/verify")


def item_event_tuples(items_list):
    tuple_list = []
    for item in items_list:
        event = {
                'summary': 'Return Deadline',
                'description': f'Return Deadline for Item: <a href="http://localhost:5000/item/{item.item_id}">http://localhost:5000/item/{item.item_id}</a>',
                'start': {
                    'date': f'{item.return_deadline}'
                },
                'end': {
                    'date': f'{item.return_deadline}'
                },
                'reminders': {
                    'useDefault': True,
                }
            }
        tuple_list.append((item, event))
    return tuple_list


@login_manager.user_loader
def load_user(user_id):
    return crud.get_user_by_id(user_id)


@app.context_processor
def inject_client_id():
    """ Inject variables into all HTML templates """
    return dict(client_id=CLIENT_ID)


@app.route("/")
def login_page():
    if not flask_login.current_user.is_authenticated:
        return render_template("login.html")
    else:
        return redirect("/dashboard")


@app.route("/verify", methods=['GET', 'POST'])
def verify():
    """ Verify a user on registration with their phone number  """
    if request.method == 'POST':
        phone = session.get('phone')
        code = request.form['code']
        
        return check_verification(phone, code)

    return render_template("verify.html")
    

@app.route("/tokensignin", methods=['GET', 'POST'])
def verify_token():
    """ Sign in a user using Google Sign-In  """
    token = request.form.get('credential')

    try:
        # Specify the CLIENT_ID of the app that accesses the backend
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
    """ Create an account and start account verification """
    email = request.form.get("createEmail")
    user = crud.get_user_by_email(email)

    if user:
        flash("That email is already associated with an account.", 'alert-warning')
    else:
        password = request.form.get("createPassword")
        first_name = request.form.get("firstName")
        
        channel = request.form.get("channel")
        mobile_number = request.form.get("mobileNumber")
        phone = "+1" + "".join(mobile_number.split("-"))
        session['phone'] = phone
        vsid = start_verification(phone, channel)
        
        if vsid is not None:
                # the verification code is sent to the user and the username is valid
                # redirect to verification check ("/verify")
                user = crud.create_user(email, password, first_name)
                crud.set_phone_number(user, phone)
                today = datetime.date.today().isoformat()
                session['today'] = today
                session['user_id'] = user.id           
                return redirect("/verify")
        
    return redirect("/")


@app.route("/login", methods=['GET', 'POST'])
def handle_login():
    """ Login user via Flask login or start verification for unverified account """
    email = request.form.get("userEmail")

    password = request.form.get("userPassword")
    user = crud.get_user_by_email(email)

    if user:
        if user.email == email and user.check_password(password):
            if user.verified == True:         
                today = datetime.date.today().isoformat()
                session["today"] = today
                flask_login.login_user(user)
                return redirect("/dashboard")
            else:
                session["phone"] = user.phone_number
                vsid = start_verification(session["phone"])
                if vsid is not None:
                    session['user_id'] = user.id           
                    return redirect(url_for('verify'))
    else:
        flash("Invalid login credentials.", 'alert-danger')
        return redirect("/")


@app.route("/logout")
@flask_login.login_required
def logout():
    if session.get('credentials'):
        del session['credentials']
    flask_login.logout_user()
    return redirect("/")


@app.route("/dashboard")
@flask_login.login_required
def dashboard():
    """ Display user's Dashboard of tracked Items """
    user = flask_login.current_user
    # Make sure tracked items are ordered by return_deadline
    tracked_items = [item for item in user.items if item.decision_status != "Complete"]
    tracked_items.sort(key=lambda x: x.return_deadline)
    
    plans = [item.plan for item in tracked_items if item.plan and item.decision_status != "Complete"]
    
    new_date = datetime.date.today().isoformat()
    today = datetime.date.fromisoformat(session["today"])
    if new_date != today:
        session["today"] = new_date

    deltas = []
    for item in tracked_items:
        return_deadline = item.return_deadline
        delta = return_deadline - today
        deltas.append(delta)

    return render_template("dashboard.html", user=user, tracked_items=tracked_items, plans=plans, today=today, deltas=deltas)


@app.route("/profile")
@flask_login.login_required
def show_profile():
    """ User's Profile of Past Items """
    user = crud.get_user_by_id(flask_login.current_user.id)
    completed_items = [item for item in user.items if item.decision_status == "Complete"]
    # TO-DO
    return render_template("profile.html", user=user, completed_items=completed_items)


@app.route("/item/<item_id>")
@flask_login.login_required
def item_details(item_id):
    """ Item Details Page """
    today = datetime.date.today()
    item = crud.get_item_by_id(item_id)
    days_left = item.return_deadline - today
    all_scores = [sentiment.general_sentiment_score for sentiment in item.sentiments]
    if all_scores: 
        overall_score = functools.reduce(lambda a, b: a + b, all_scores) / len(all_scores)
    else:
        overall_score = None
    return render_template("item.html", item=item, today=today, days_left=days_left, overall_score=overall_score)


@app.route("/add_item", methods=['POST'])
@flask_login.login_required
def add_item():
    """ Add an item to be tracked by Mindful """
    user = crud.get_user_by_id(flask_login.current_user.id)
    return_deadline = request.form.get("return_deadline")
    return_type = request.form.get("return_type")
    brand = request.form.get("brand")
    retailer_name = request.form.get("retailer")
    price = request.form.get("price")

    if not crud.get_retailer_by_name(user, retailer_name):
        returns_url = request.form.get("returns_url")
        retailer = crud.create_retailer(name=retailer_name, returns_url=returns_url)
    else:
        retailer = crud.get_retailer_by_name(user, retailer_name)
    
    item = crud.create_item(user.id, retailer.retailer_id, brand, price, return_deadline, return_type)
    
    text = request.form.get("text")
    email = request.form.get("email")
    crud.set_item_reminders(item, text, email)

    file = request.files["image"]
    image = crud.create_image(item)
    result = cloudinary.uploader.upload(file, api_key=CLOUDINARY_KEY, api_secret=CLOUDINARY_SECRET, cloud_name=CLOUD_NAME, folder=f'mindful/{user.id}/')
    img_url = result['secure_url']
    crud.add_image_url(image, img_url)

    return redirect("/dashboard")


@app.route("/item/<item_id>/enter_reflection", methods=['POST'])
@flask_login.login_required
def add_sentiment(item_id):
    item = crud.get_item_by_id(item_id)
    previous_sentiments = item.sentiments
    today = datetime.date.today().isoformat()

    # Commenting out code that limits reflection entries to once per day per item
    #
    # today = datetime.date.fromisoformat(session["today"])
    # if new_date != today:
    #     session["today"] = new_date
    #     today = session["today"]
    
    # if previous_sentiments:
    #     if previous_sentiments[-1].date == today:
    #         flash("Today's reflection has already been entered!", "alert-warning")
    #         return redirect(f"/item/{item_id}")
    
    entry = request.form.get("reflection")
    
    try:
        response = natural_language_understanding.analyze(text=entry, features=Features(
            entities=EntitiesOptions(emotion=True, sentiment=True, limit=2),
            emotion=EmotionOptions(targets=['item', 'fit', 'size', 'value', 
            'worth', 'keep', 'return', 'quality', 'wear', 'color']),
            keywords=KeywordsOptions(emotion=True, sentiment=True, limit=3),
            sentiment=SentimentOptions(targets=['item', 'fit', 'size', 'value', 
            'worth', 'keep', 'return', 'quality', 'wear', 'color']))).get_result()
    except:
        flash("Unable to generate sentiment analysis from text entered, please try again.", "alert-warning")
        return redirect(f"/item/{item_id}")
    
    # For debugging
    # response_dump = json.dumps(response, indent=2)
    # print(response_dump)

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
            flash("Unable to generate sentiment analysis from text entered, please try again.", "alert-warning")
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
        flash("This item had a plan in progress.", "alert-warning")

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
    user = crud.get_user_by_id(flask_login.current_user.id)
    gmaps_key = os.environ["gmaps_key"]

    return render_template("plan.html", plan=plan, item=item, gmaps_key=gmaps_key, user=user)


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


@app.route("/item/<item_id>/send_offer", methods=['POST'])
@flask_login.login_required
def send_offer(item_id):
    item = crud.get_item_by_id(item_id)
    user = crud.get_user_by_id(flask_login.current_user.id)

    name = request.form.get("recipient_name")
    email = request.form.get("recipient_email")
    mobile_input = request.form.get("recipient_mobile")

    offer_message = request.form.get("message")
    
    if not offer_message:
        offer_message = f'Hello {name}, this is Mindful. {user.first_name} has been reflecting on their recent purchase from {item.retailer.name}, and has decided to give the item a second life. They would like to gift you this item! Feel free to let {{user.first_name}} know if you would like to accept or decline.'
    
    if mobile_input:
        phone_number = "+1" + "".join(mobile_input.split("-"))
        text = client.messages \
                    .create(
                        body=offer_message,
                        from_=TWILIO_PHONE_NUMBER,
                        to=phone_number
                    )
    if email:
        message = Mail(
        from_email='lizcodingdev@gmail.com',
        to_emails=email,
        subject='Mindful Gift Offer',
        html_content=offer_message)
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)
    
    flash("Offer Sent!", "alert-success")

    return redirect(f"/item/{item.item_id}")


@app.route("/journal")
@flask_login.login_required
def journal():
    user = crud.get_user_by_id(flask_login.current_user.id)
    #TO-DO
    return render_template("journal.html")


@app.route("/authorize_calendar")
@flask_login.login_required
def authorize_calendar():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=CALENDAR_SCOPES)

  # The URI created here must exactly match one of the authorized redirect URIs
  # for the OAuth 2.0 client, which you configured in the API Console. If this
  # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
  # error.
  flow.redirect_uri = url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission.
      access_type='offline',
      # Disable incremental authorization. Enable is recommended as a best practice.
      include_granted_scopes='false')

  # Store the state so the callback can verify the auth server response.
  session['state'] = state

  return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = session['state']

  flow = Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=CALENDAR_SCOPES, state=state)
  flow.redirect_uri = url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  credentials = flow.credentials
  session['credentials'] = credentials_to_dict(credentials)

  return redirect("/calendar")


@app.route("/calendar")
@flask_login.login_required
def calendar():
    if not session.get('credentials'):
        return redirect('/authorize_calendar')
    user = crud.get_user_by_id(flask_login.current_user.id)

    # Load credentials from the session.
    credentials = Credentials(**session['credentials'])

    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    if not user.calendar:
        calendar = {
        'summary': 'Mindful',
        'timeZone': 'America/Los_Angeles'
        }
        google_calendar = service.calendars().insert(body=calendar).execute()
        crud.create_calendar(user, google_calendar['id'])

    calendar = user.calendar[0]

    if calendar.items:
        unadded_items = [item for item in user.items if item.return_deadline and item.decision_status != 'Complete' and item not in calendar.items]
    else:
        unadded_items = [item for item in user.items if item.decision_status != 'Complete']
    
    if unadded_items:
        # item_event tuples returns a tuple of (item, event)
        unadded_events = item_event_tuples(unadded_items)
        for event_tuple in unadded_events:
            item = event_tuple[0]
            event = event_tuple[1]
            calendarId = calendar.calendar_id
            added_event = service.events().insert(calendarId=calendarId, body=event).execute()
            crud.add_calendar_item(item, calendar, added_event)

    removed_items = [item for item in calendar.items if item.decision_status == 'Complete']

    for item in removed_items:
        service.events().delete(calendarId='Mindful', eventId=f'{item.event_id}').execute()
        crud.remove_item_from_calendar(item)


    # Save credentials back to session in case access token was refreshed.
    session['credentials'] = credentials_to_dict(credentials)
    
    return render_template("calendar.html", user=user, calendar_id=calendar.calendar_id, calendar_items=calendar.items)


if __name__ == "__main__":
    # When running locally, disable OAuthlib's HTTPs verification.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)
