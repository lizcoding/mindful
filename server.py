from flask import (Flask, redirect, flash, request, render_template, session)
from jinja2 import StrictUndefined
from model import connect_to_db
import os
import crud
import cloudinary.uploader


app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined

# Required to use Flask sessions
app.secret_key = os.environ['MINDFUL_KEY']

# Configure Cloudinary API
CLOUD_NAME = os.environ['CLOUD_NAME']
CLOUDINARY_KEY = os.environ['CLOUD_KEY']
CLOUDINARY_SECRET = os.environ['CLOUD_SECRET']


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
    tracked_items = [item for item in user.items if item.decision_status == "Undecided"]
    # TO-DO 
    plans = [ ]
    
    # TO-DO
    
    return render_template("dashboard.html", user=user, tracked_items=tracked_items, plans=plans)
    

@app.route("/item/<item_id>")
def item_details(item_id):
    if not session.get("user_id"):
        return redirect("/")
    item = crud.get_item_by_id(item_id)

    # TO-DO

    return render_template("item.html", item=item)


@app.route("/add_item", methods=['POST'])
def add_item():
    if not session.get("user_id"):
        return redirect("/")
    
    user = crud.get_user_by_id(session["user_id"])
    item_url = request.form.get("item_url") 
    retailer_name = request.form.get("retailer")
    
    if not crud.get_retailer_by_name(user, retailer_name):
        main_url = request.form.get("main_url")
        returns_url = request.form.get("returns_url")
        return_window = int(request.form.get("return_window"))
        retailer = crud.create_retailer(name=retailer_name, main_url=main_url, returns_url=returns_url, return_window=return_window)
    else:
        retailer = crud.get_retailer_by_name(user, retailer_name)
    
    item = crud.create_item(user.user_id, retailer.retailer_id, item_url)
    
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
    # if not session.get("user_id"):
    #     return redirect("/")
    # user = crud.get_user_by_id(session["user_id"])
    # item = crud.get_item_by_id(item_id)

    # # TO-DO: Code full Item object update

    return redirect(f"/item/{item_id}")


@app.route("/item/<item_id>/add_plan", methods=['POST'])
def add_plan(item_id):
    if not session.get("user_id"):
        return redirect("/")
    action = request.form.get("action")

    # TO-DO: Code full Plan object instantiation

    crud.create_plan(item_id, action=action)
    return redirect("/dashboard")


@app.route("/plan/<plan_id>")
def plan_details(plan_id):
    if not session.get("user_id"):
        return redirect("/")
    plan = crud.get_plan_by_id(plan_id)
    
    # TO-DO

    return render_template("plan.html", plan=plan)


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
