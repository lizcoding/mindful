from flask import Flask, redirect, flash, request, render_template, session
from jinja2 import StrictUndefined
from model import connect_to_db
import crud
import secrets
import cloudinary


app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True

# Required to use Flask sessions
app.secret_key = secrets.MINDFUL_KEY

# Configure Cloudinary API
cloudinary.config( 
  cloud_name = secrets.cloud_name, 
  api_key = secrets.api_key, 
  api_secret = secrets.api_secret
)

@app.route("/")
def show_login():
    return render_template("login.html")


@app.route("/create_account", methods=["POST"])
def register_user():
    email = request.form.get("email")
    password = request.form.get("password")
    user = crud.get_user_by_email(email)

    if user:
        flash("That email is already associated with an account.")
    else:
        crud.create_user(email, password)
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
    if not session.get("user"):
        return redirect("/")

    user = crud.get_user_by_id(session["user_id"])
    tracked_items = [item for item in user.items if item.decision_status == "Undecided"]
    plans = user.plans
    
    # TO-DO
    
    return render_template("dashboard.html", user=user, tracked_items=tracked_items, plans=plans)
    

@app.route("/item/<item_id>")
def item_details(item_id):
    if not session.get("user"):
        return redirect("/")
    item = crud.get_item_by_id(item_id)

    # TO-DO

    return render_template("item.html", item=item)


@app.route("/add_item", methods=['POST'])
def add_item():
    if not session.get("user"):
        return redirect("/")
    user = crud.get_user_by_id(session["user_id"])
    retailer = request.form.get("retailer")

    # TO-DO: Code full Item object instantiation
    
    crud.create_item(user.user_id, retailer)
    return redirect("/dashboard")


@app.route("/item/<item_id>/add_detail", methods=['POST'])
def add_detail(item_id):
    # if not session.get("user"):
    #     return redirect("/")
    # user = crud.get_user_by_id(session["user_id"])
    # item = crud.get_item_by_id(item_id)

    # # TO-DO: Code full Item object update

    return redirect(f"/item/{item_id}")


@app.route("item/<item_id>/add_plan", methods=['POST'])
def add_plan(item_id):
    if not session.get("user"):
        return redirect("/")
    action = request.form.get("action")

    # TO-DO: Code full Plan object instantiation

    crud.create_plan(item_id, action=action)
    return redirect("/dashboard")


@app.route("/plan/<plan_id>")
def plan_details(plan_id):
    if not session.get("user"):
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
    app.run(
        host="0.0.0.0",
        use_reloader=True,
        use_debugger=True,
    )

