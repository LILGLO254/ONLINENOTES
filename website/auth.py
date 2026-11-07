
from urllib.parse import urlparse

import psycopg
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from . import limiter
from .models import User, create_connection, get_user_by_email

auth = Blueprint("auth", __name__)


def is_safe_next_url(target):
    parsed = urlparse(target)
    return (
        bool(parsed.path)
        and parsed.path.startswith("/")
        and not parsed.path.startswith("//")
        and not parsed.scheme
        and not parsed.netloc
    )


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html",
                error="Incorrect email or password.",
                email_value=email
            )

        user_data = get_user_by_email(email)

        if (
            user_data is None
            or not check_password_hash(
                user_data["password"], password
            )
        ):
            return render_template(
                "login.html",
                error="Incorrect email or password.",
                email_value=email
            )

        user = User(
            user_id=user_data["user_id"],
            username=user_data["user_name"],
            email=user_data["email"]
        )

        login_user(user)

        next_url = request.args.get("next", "")
        if is_safe_next_url(next_url):
            return redirect(next_url)
        return redirect(url_for("views.home"))

    return render_template("login.html", email_value="")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out successfully.", category ="success")
    return redirect(url_for("auth.login"))


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        first_name = request.form.get("FirstName", "").strip()
        password1 = request.form.get("password1", "")
        password2 = request.form.get("password2", "")

        if not email or not first_name or not password1 or not password2:
            flash("Please fill in all fields.",category = "error")
            return redirect(url_for("auth.signup"))

        if (
            len(email) < 7
            or email.count("@") != 1
            or email.startswith("@")
            or email.endswith("@")
        ):
            flash("Please enter a valid email address.",category =  "error")
            return redirect(url_for("auth.signup"))

        if len(first_name) < 2:
            flash("Name must contain at least 2 characters.",category = "error")
            return redirect(url_for("auth.signup"))

        if password1 != password2:
            flash("Passwords do not match.",category = "error")
            return redirect(url_for("auth.signup"))

        if len(password1) < 8:
            flash("Password must be at least 8 characters.",category = "error")
            return redirect(url_for("auth.signup"))

        connection = None
        cursor = None

        try:
            connection = create_connection()
            cursor = connection.cursor()

            hashed_password = generate_password_hash(password1)

            cursor.execute(
                """
                INSERT INTO users (user_name, email, password)
                VALUES (%s, %s, %s)
                """,
                (first_name, email, hashed_password)
            )

            connection.commit()

            flash("Account created successfully. Please log in.", category = "success")
            return redirect(url_for("auth.login"))

        except psycopg.errors.UniqueViolation:
            if connection:
                connection.rollback()

            flash("That email address already exists.", "error")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("signup.html")
