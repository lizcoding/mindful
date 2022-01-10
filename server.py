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
def show_dashboard():
    user = crud.get_user_by_id(session["user_id"])
    
    # TO-DO

    return render_template("dashboard.html")


@app.route("/profile")
def show_profile():
    user = crud.get_user_by_id(session["user_id"])
    
    # TO-DO

    return render_template("profile.html")


@app.route("/item/<item_id>")
def focus_item(item_id):
    user = crud.get_user_by_id(session["user_id"])

    # TO-DO

    return render_template("item.html", item=item_id)


@app.route("/plan/<plan_id>")
def focus_item(plan_id):
    user = crud.get_user_by_id(session["user_id"])

    # TO-DO

    return render_template("plan.html", plan=plan_id)


if __name__ == "__main__":
    connect_to_db(app)
    app.run(
        host="0.0.0.0",
        use_reloader=True,
        use_debugger=True,
    )

