from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from functools import wraps
from database import start_connection
import sqlite3

patient_blueprint = Blueprint(
    "patient",
    __name__,
    url_prefix="/patient",
    template_folder="../templates/patient"
)

#It make sure that only logged-in patients can access certain routes
def patient_required(fn):
    @wraps(fn)
    def secured_route(*args, **kwargs):
        if session.get("role") != "patient":
            flash("Please login as a patient to continue.", "error")
            return redirect("/login")
        return fn(*args, **kwargs)
    return secured_route

#It fetch logged-in patient record
def fetch_logged_patient():
    user_id = session.get("user_ref")

    db = start_connection()
    cur = db.cursor()

    cur.execute("SELECT * FROM patients WHERE user_ref = ?", (user_id,))
    return cur.fetchone()


#Patient Dashboard
@patient_blueprint.route("/dashboard")
@patient_required
def dashboard():
    patient = fetch_logged_patient()

    db = start_connection()
    cur = db.cursor()

    #Upcoming appointments
    cur.execute("""
        SELECT a.*, d.name AS doctor_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = ? AND a.status = 'Booked'
        ORDER BY date(a.date) ASC
    """, (patient["id"],))
    upcoming_apts = cur.fetchall()

    #S hows completed appointments with treatment details
    cur.execute("""
        SELECT a.*, d.name AS doctor_name, t.diagnosis, t.prescription
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        LEFT JOIN treatments t ON t.appointment_id = a.id
        WHERE a.patient_id = ? AND a.status = 'Completed'
        ORDER BY date(a.date) DESC
    """, (patient["id"],))
    past_apts = cur.fetchall()

    return render_template(
        "patient/dashboard.html",
        patient=patient,
        upcoming=upcoming_apts,
        past=past_apts
    )


#Search Doctors
@patient_blueprint.route("/search", methods=["GET", "POST"])
@patient_required
def search():
    db = start_connection()
    cur = db.cursor()
    results = []

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        specialization = request.form.get("specialization", "").strip()

        cur.execute("""
            SELECT *
            FROM doctors
            WHERE name LIKE ? AND specialization LIKE ?
        """, (f"%{name}%", f"%{specialization}%"))
        results = cur.fetchall()

    return render_template("patient/search.html", doctors=results)


#Appointment Booking
@patient_blueprint.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@patient_required
def book_appointment(doctor_id):
    patient = fetch_logged_patient()
    db = start_connection()
    cur = db.cursor()

    cur.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,))
    doctor = cur.fetchone()
    if not doctor:
        flash("Doctor not found", "error")
        return redirect(url_for("patient.search"))

    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")

        # Basic validation
        if not date or not time:
            flash("Please provide date and time.", "error")
            return redirect(url_for("patient.book", doctor_id=doctor_id))

        try:
            # Start immediate transaction to get a RESERVED lock (prevents concurrent writers)
            db.execute("BEGIN IMMEDIATE")
            # Re-check existing appointment for same doctor/date/time
            cur.execute("""
                SELECT id FROM appointments
                WHERE doctor_id=? AND date=? AND time=? AND status='Booked'
            """, (doctor_id, date, time))
            existing = cur.fetchone()
            if existing:
                db.execute("ROLLBACK")
                flash("This slot was just taken by someone else. Please choose another slot.", "error")
                return redirect(url_for("patient.book", doctor_id=doctor_id))

            # Insert appointment
            try:
                cur.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, date, time, status)
                    VALUES (?, ?, ?, ?, 'Booked')
                """, (patient["id"], doctor_id, date, time))
                db.commit()
                flash("Appointment booked successfully!", "success")
            except Exception as e:
                # Unique index may reject duplicate inserts
                db.execute("ROLLBACK")
                flash("Could not book slot — it may have been taken. Try another slot.", "error")
            return redirect(url_for("patient.dashboard"))
        except sqlite3.OperationalError:
            # Lock failed (rare) — fall back
            flash("Server busy, try again in a moment.", "warning")
            return redirect(url_for("patient.book", doctor_id=doctor_id))
    return render_template("patient/book.html", doctor=doctor)




#Edit existing appointment
@patient_blueprint.route("/edit/<int:apt_id>", methods=["GET", "POST"])
@patient_required
def edit_appointment(apt_id):
    db = start_connection()
    cur = db.cursor()

    cur.execute("""
        SELECT a.*, d.name AS doctor_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.id = ?
    """, (apt_id,))
    apt = cur.fetchone()

    if not apt:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient.dashboard"))

    if request.method == "POST":
        new_date = request.form.get("date")
        new_time = request.form.get("time")

        #Avoids double-booking
        cur.execute("""
            SELECT id FROM appointments
            WHERE doctor_id = ? AND date = ? AND time = ? AND status = 'Booked'
        """, (apt["doctor_id"], new_date, new_time))
        conflict = cur.fetchone()

        if conflict:
            flash("The selected time slot is unavailable.", "error")
            return redirect(url_for("patient.edit_appointment", apt_id=apt_id))

        cur.execute("""
            UPDATE appointments
            SET date = ?, time = ?
            WHERE id = ?
        """, (new_date, new_time, apt_id))
        db.commit()

        flash("Appointment updated successfully.", "success")
        return redirect(url_for("patient.dashboard"))

    return render_template("patient/edit.html", apt=apt)


#Cancels an appointment
# controllers/patient_controller.py — cancel route
@patient_blueprint.route("/cancel/<int:apt_id>")
@patient_required
def cancel(apt_id):
    db = start_connection()
    cur = db.cursor()
    # verify ownership
    cur.execute("SELECT * FROM appointments WHERE id=?", (apt_id,))
    apt = cur.fetchone()
    if not apt:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient.dashboard"))
    # ensure patient owns it
    patient = fetch_logged_patient()
    if apt["patient_id"] != patient["id"]:
        flash("Unauthorized", "error")
        return redirect(url_for("patient.dashboard"))

    cur.execute("UPDATE appointments SET status='Cancelled' WHERE id=?", (apt_id,))
    db.commit()
    flash("Appointment cancelled and slot freed.", "info")
    return redirect(url_for("patient.dashboard"))



#Update Patient Profile
@patient_blueprint.route("/profile", methods=["GET", "POST"])
@patient_required
def update_profile():
    patient = fetch_logged_patient()

    db = start_connection()
    cur = db.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        contact = request.form.get("contact")
        email = request.form.get("email")

        cur.execute("""
            UPDATE patients
            SET name = ?, age = ?, gender = ?, contact = ?, email = ?
            WHERE id = ?
        """, (name, age, gender, contact, email, patient["id"]))
        db.commit()

        flash("Profile details updated.", "success")
        return redirect(url_for("patient.update_profile"))

    return render_template("patient/profile.html", patient=patient)
