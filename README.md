# Mindful
About Mindful

## Contents
* [Tech Stack](#technologies)
* [Features](#features)
* [Installation](#install)

## <a name="technologies"></a>Tech Stack
Backend: Python, Flask, PostgreSQL, SQLAlchemy
Frontend: JavaScript, Jinja2, Bootstrap, HTML5, CSS3
APIs: Cloudinary, Google Sign-In, Google Maps, Google Calendar, IBM Watson Natural Language Understanding, Twilio Verify, Twilio SMS, Twilio Sengrid
Libraries: Flask Login

## <a name="features"></a>Features

Mindful's features include a reflection journal, Google Calendar integration, Google Sign-in, account phone verification, Google Maps display and directions, and text/email for notifying friends via Mindful.



## <a name="install"></a>Installation

To run Mindful:

Install PostgreSQL (Mac OSX)

Clone or fork this repo:

```
https://github.com/lizcoding/mindful
```

Create and activate a virtual environment inside your Mindful directory:

```
virtualenv env
source env/bin/activate
```

Install the dependencies:

```
pip3 install -r requirements.txt
```

Sign up to use the [IBM Watson Natural Language Understanding API](https://www.ibm.com/cloud/watson-natural-language-understanding), [Twilio SMS API](https://www.twilio.com/sms), [Twilio SendGrid API](https://www.twilio.com/sendgrid/email-api), [Cloudinary API]( cloudinary.com), [Google Maps API](https://developers.google.com/maps/documentation/javascript/overview), and [Google Calendar API](https://developers.google.com/calendar/api). Make sure the Google Maps Javascript API, Places API, and Calendar API, and Cloud Identity API are activated in your Google Developer Console.

Obtain OAuth 2.0 credentials from the Google API Console(https://console.developers.google.com/). Authorize the following origins:
```
http://localhost
http://localhost:5000
```

Authorize the following redirect URIs:
```
http://localhost:5000/token_signin
http://localhost:5000/dashboard
```

Save your API keys in a file called <kbd>secrets.sh</kbd> using this format:

```
# Mindful App Key
export MINDFUL_KEY="YOUR_KEY_HERE"

# Google Maps Key
export gmaps_key="YOUR_KEY_HERE"

# Cloudinary Key
export CLOUD_NAME="YOUR_NAME_HERE"
export CLOUD_KEY="YOUR_KEY_HERE"
export CLOUD_SECRET="YOUR_SECRET_HERE"

# IBM Natural Language Understanding Key
export IBM_NATURAL_LANGUAGE_KEY="YOUR_KEY_HERE"
export IBM_NATURAL_LANGUAGE_URL="YOUR_URL_HERE"

# Twilio Key
export TWILIO_ACCOUNT_SID="YOUR_SID_HERE"
export TWILIO_SECRET="YOUR_SECRET_HERE"
export TWILIO_AUTH_TOKEN="YOUR_TOKEN_HERE"
export TWILIO_PHONE_NUMBER="YOUR_NUMBER_HERE"
export VERIFY_SERVICE_SID="YOUR_SID_HERE"
export SENDGRID_API_KEY="YOUR_KEY_HERE"

# Google OAuth
export client_id="YOUR_ID_HERE"
export client_secret="YOUR_SECRET_HERE"

# Google Calendar
export client_secrets_file="YOUR_FILENAME_HERE"
```

Source your keys from your secrets.sh file into your virtual environment:

```
source secrets.sh
```

Setup the database:

```
createdb mindful
python -i model.py
db.create_all()
quit()
```

Run the app:

```
python server.py
```

You can now navigate to 'localhost:5000/' to access Mindful.
