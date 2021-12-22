from flask import Flask, redirect, request, render_template, session
from jinja2 import StrictUndefined
import secrets


app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True

# Required to use Flask sessions
app.secret_key = secrets.MINDFUL_KEY


@app.route("/")
def show_login():
    return render_template("login.html")


@app.route("/dashboard")
def show_dashboard():
    return render_template("dashboard.html")


@app.route("/profile")
def show_profile():
    return render_template("profile.html")


@app.route("/item/<int:item_id>")
def focus_item(item_id):
    return render_template("item.html", item=item_id)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        use_reloader=True,
        use_debugger=True,
    )

