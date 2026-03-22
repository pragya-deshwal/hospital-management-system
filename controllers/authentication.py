from flask import Blueprint, render_template, request, redirect, session, flash
from database import start_connection

authentication_blueprint = Blueprint("authentication", __name__)

#This will handle patient registration
@authentication_blueprint.route("/register", methods=["GET", "POST"])
def patient_registration():
    if request.method == "POST":

    #It will get data from the registration form
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        contact = request.form.get("contact")
        username = request.form.get("username")
        password = request.form.get("password")

        conn = start_connection()
        cur = conn.cursor()

    #It will insert data into users and patients table
        try:
            cur.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, 'patient')
            """, (username, password))
            conn.commit()
        except:
            flash("This username already exists, try another username!", "error")
            return redirect("/register")

    #Get the user id of the newly created user only
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        user_record = cur.fetchone()
        new_user_ref = user_record["id"]

    #It will insert data into patients table
        cur.execute("""
            INSERT INTO patients (name, age, gender, contact, user_ref)
            VALUES (?, ?, ?, ?, ?)
        """, (name, age, gender, contact, new_user_ref))
        conn.commit()

        flash("Your registration has been done. Now please log in!", "success")
        return redirect("/login")

    return render_template("registration.html")


#User (admin/doctor/patient) login
@authentication_blueprint.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = start_connection()
        cur = conn.cursor()

    #It will find the user
        cur.execute("""
            SELECT * FROM users WHERE username=? AND password=?
        """, (username, password))
        user = cur.fetchone()

        if user:
            session["user_ref"] = user["id"]
            session["role"] = user["role"]

        #Redirects according to the user role
            if user["role"] == "admin":
                return redirect("/admin/dashboard")
            elif user["role"] == "doctor":
                return redirect("/doctor/dashboard")
            else:
                return redirect("/patient/dashboard")

        flash("Your username or password is incorrect!", "error")
        return redirect("/login")

    return render_template("login.html")


#It will logout the user
@authentication_blueprint.route("/logout")
def user_logout():
    session.clear()
    return redirect("/login")
