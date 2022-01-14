from flask import (Flask, redirect, flash, request, render_template, session)
from jinja2 import StrictUndefined
from model import connect_to_db
import os
import crud
import datetime
import cloudinary.uploader

# TO-DO: 1/14
# TO-DO: [ ] Add price attribute to Item objects (edit DB)
# TO-DO: [ ] Add entry date attribute to Sentiment objects (edit DB)
# TO-DO: [ ] Ensure Sentiment object instantiation from form submission

# TO-DO: [ ] Change "Status" when plan has been added + when plan has been executed
# TO-DO: [ ] Remove "Add Details", "Add Plan" forms for items with existing details/plans
# TO-DO: [X] Add "Days Left" displays in the Dashboard
# TO-DO: [ ] Create Profile route for non-tracked items (items that finished Mindful track-plan life-cycle)
# TO-DO: [ ] Order items/plans on dashboard by time-sensitivity (Days left)
# TO-DO: [ ] Show top 3 time-sensitive items or plans at the very top of the page

# END OF MVP: IMB Watson integration up and running
# TO-DO: [ ] Screen capture walk through of MVP

# On the horizon: OAuth login

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.filters['zip'] = zip

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
    
    today = session.get("today")
    return render_template("dashboard.html", user=user, tracked_items=tracked_items, plans=plans, today=today, deltas=deltas)
    

@app.route("/item/<item_id>")
def item_details(item_id):
    if not session.get("user_id"):
        return redirect("/")
    item = crud.get_item_by_id(item_id)

    return render_template("item.html", item=item)


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

    if not crud.get_retailer_by_name(user, retailer_name):
        main_url = request.form.get("main_url")
        returns_url = request.form.get("returns_url")
        return_window = int(request.form.get("return_window"))
        retailer = crud.create_retailer(name=retailer_name, main_url=main_url, returns_url=returns_url, return_window=return_window)
    else:
        retailer = crud.get_retailer_by_name(user, retailer_name)
    
    item = crud.create_item(user.user_id, retailer.retailer_id, brand, item_url, return_deadline, return_type)
    
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
    entry = request.form.get("reflection")
    analysis = ""
    score = ""
    crud.create_sentiment(item_id, entry, analysis, score)

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
