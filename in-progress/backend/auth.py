import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection

# Blueprint so you can keep auth routes in a separate file
auth_bp = Blueprint("auth", __name__)

# Register
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles the Create Account page.
    GET  -> show empty form
    POST -> validate inputs, insert new user into User_T
    """
    if request.method == "POST":
        # Read form fields
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username:
            username = email

        # Basic validation
        if not email or not password or not username:
            flash("Please fill out all required fields.")
            return redirect(url_for("auth.register"))

        # Enforce minimum password length (project requirement)
        if len(password) < 6:
            flash("Password must be at least 6 characters long.")
            return redirect(url_for("auth.register"))

        # Open DB connection
        conn = get_connection()
        cur = conn.cursor()

        # 1) Check if username already exists
        cur.execute("SELECT 1 FROM User_T WHERE LOWER(Username) = LOWER(?)", (username,))
        if cur.fetchone() is not None:
            conn.close()
            flash("That username is already taken.")
            return redirect(url_for("auth.register"))

        # 2) Get next UserID (MAX + 1)
        cur.execute("SELECT COALESCE(MAX(UserID), 0) + 1 AS NextID FROM User_T")
        next_id = cur.fetchone()["NextID"]

        # 3) Insert new user as regular 'User'
        insert_sql = """
            INSERT INTO User_T (UserID, Username, Password, Name, UserType, Email)
            VALUES (?, ?, ?, ?, 'User', ?)
        """
        cur.execute(insert_sql, (next_id, username, password, name, email))

        # Save changes
        conn.commit()
        conn.close()

        flash("Registration successful! You can now log in.")
        return redirect(url_for("auth.login"))

    # If GET request, just show the template
    return render_template("register.html")
    # Make sure you have templates/register.html


# Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles the Log In page.
    GET  -> show login form
    POST -> check credentials against User_T
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please enter both username and password.")
            return redirect(url_for("auth.login"))

        conn = get_connection()
        cur = conn.cursor()

        # Look for matching username + password
        query = """
            SELECT UserID, Username, UserType
            FROM User_T
            WHERE LOWER(Username) = LOWER(?) AND Password = ?
        """
        cur.execute(query, (username, password))
        row = cur.fetchone()
        conn.close()

        if row:
            # Store user info in session so the rest of the app knows who is logged in
            session["user_id"] = row["UserID"]
            session["username"] = row["Username"]
            session["user_type"] = row["UserType"]  # 'Admin' or 'User'
            session["is_admin"] = (row["UserType"] == "Admin")

            flash("Login successful!")

            # Route based on role
            if session["is_admin"]:
                return redirect(url_for("admin.dashboard"))  # admin landing page
            else:
                return redirect(url_for("shop.shop_home"))   # main catalog page

        # If no row matched:
        flash("Incorrect username or password.")
        return redirect(url_for("auth.login"))

    # GET -> show login template
    return render_template("login.html")
    # Make sure you have templates/login.html


# LOGOUT
@auth_bp.route("/logout")
def logout():
    """
    Logs the user out by clearing the session.
    """
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("user_type", None)
    session.pop("is_admin", None)
    flash("You have been logged out.")
    return redirect(url_for("shop.shop_home"))  # or home page
