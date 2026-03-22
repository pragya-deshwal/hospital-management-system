from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from database import start_connection
from datetime import datetime, timedelta
from functools import wraps

doctor_blueprint = Blueprint(
    "doctor",
    __name__,
    url_prefix="/doctor"
)

#Allows access only to the doctors
def doctor_required(view_function):
    @wraps(view_function)
    def secure_view(*args, **kwargs):
        if session.get("role") != "doctor":
            flash("Access denied! Doctor login is required.", "error")
            return redirect("/login")
        return view_function(*args, **kwargs)
    return secure_view


#It fetchs logged-in doctor's record using session user_id
def get_logged_in_doctor():
    user_id = session.get("user_ref")
    if not user_id:
        return None

    conn = start_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM doctors WHERE user_ref = ?", (user_id,))
    return cur.fetchone()

#Doctor Dashboard
@doctor_blueprint.route("/dashboard")
@doctor_required
def dashboard():
    doctor = get_logged_in_doctor()

    if not doctor:
        flash("Doctor profile missing. Contact admin.", "error")
        return redirect("/login")

    conn = start_connection()
    cur = conn.cursor()

    #upcoming week range
    today = datetime.utcnow().date()
    next_week = today + timedelta(days=7)

    cur.execute("""
        SELECT a.id, a.date, a.time, a.status,
               p.name AS patient_name
        FROM appointments AS a
        JOIN patients AS p ON a.patient_id = p.id
        WHERE a.doctor_id = ?
        AND date(a.date) BETWEEN date(?) AND date(?)
        ORDER BY a.date, a.time
    """, (doctor["id"], today.isoformat(), next_week.isoformat()))
    upcoming_appointments = cur.fetchall()

    #recent 20 patients
    cur.execute("""
        SELECT DISTINCT p.id, p.name, p.age, p.gender
        FROM appointments AS a
        JOIN patients AS p ON a.patient_id = p.id
        WHERE a.doctor_id = ?
        ORDER BY a.id DESC
        LIMIT 20
    """, (doctor["id"],))
    recent_patients = cur.fetchall()

    return render_template(
        "doctor/dashboard.html",
        doctor=doctor,
        upcoming=upcoming_appointments,
        patients=recent_patients
    )

#View all appointments
@doctor_blueprint.route("/appointments")
@doctor_required
def appointments_list():
    doctor = get_logged_in_doctor()

    if not doctor:
        flash("Doctor profile missing.", "error")
        return redirect("/login")

    conn = start_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.id, a.date, a.time, a.status,
               p.name AS patient_name
        FROM appointments AS a
        JOIN patients AS p ON a.patient_id = p.id
        WHERE a.doctor_id = ?
        ORDER BY a.date DESC, a.time DESC
    """, (doctor["id"],))

    appointments = cur.fetchall()

    return render_template(
        "doctor/appointments.html",
        doctor=doctor,
        appointments=appointments
    )

#Appointment Details Page
@doctor_blueprint.route("/appointment/<int:appointment_id>", methods=["GET", "POST"])
@doctor_required
def appointment_details(appointment_id):
    doctor = get_logged_in_doctor()
    if not doctor:
        flash("Doctor profile missing.", "error")
        return redirect("/login")

    conn = start_connection()
    cur = conn.cursor()

    #It loads appointment details
    cur.execute("""
        SELECT a.*, 
               p.name AS patient_name,
               p.age AS patient_age,
               p.gender AS patient_gender
        FROM appointments AS a
        JOIN patients AS p ON a.patient_id = p.id
        WHERE a.id = ?
    """, (appointment_id,))
    appointment = cur.fetchone()

    if not appointment:
        flash("Appointment not found.", "error")
        return redirect(url_for("doctor.appointments_list"))

    #Make sure that the appointment belongs to doctor
    if appointment["doctor_id"] != doctor["id"]:
        flash("Unauthorized access!", "error")
        return redirect(url_for("doctor.appointments_list"))

    #It fetch existing treatment entry
    cur.execute("SELECT * FROM treatments WHERE appointment_id = ?", (appointment_id,))
    treatment_record = cur.fetchone()

    #It update or cancel appointment
    if request.method == "POST":
        action = request.form.get("action")

        if action == "cancel":
            cur.execute(
                "UPDATE appointments SET status='Cancelled' WHERE id=?",
                (appointment_id,)
            )
            conn.commit()
            flash("Appointment cancelled.", "info")
            return redirect(url_for("doctor.appointments_list"))

        if action == "complete":
            diagnosis = request.form.get("diagnosis", "")
            prescription = request.form.get("prescription", "")
            notes = request.form.get("notes", "")

            #Mark appointment as completed
            cur.execute(
                "UPDATE appointments SET status='Completed' WHERE id=?",
                (appointment_id,)
            )

            #Update or add treatment record
            if treatment_record:
                cur.execute("""
                    UPDATE treatments
                    SET diagnosis=?, prescription=?, notes=?
                    WHERE appointment_id=?
                """, (diagnosis, prescription, notes, appointment_id))
            else:
                cur.execute("""
                    INSERT INTO treatments (appointment_id, diagnosis, prescription, notes)
                    VALUES (?, ?, ?, ?)
                """, (appointment_id, diagnosis, prescription, notes))

            conn.commit()
            flash("Treatment saved & appointment completed.", "success")
            return redirect(url_for("doctor.appointments_list"))

    return render_template(
        "doctor/appointment_detail.html",
        doctor=doctor,
        appointment=appointment,
        treatment=treatment_record
    )

#Updates the availability of the doctor
@doctor_blueprint.route("/availability", methods=["GET", "POST"])
@doctor_required
def update_availability():
    doctor = get_logged_in_doctor()

    if not doctor:
        flash("Doctor profile missing.", "error")
        return redirect("/login")

    conn = start_connection()
    cur = conn.cursor()

    if request.method == "POST":
        availability_text = request.form.get("availability", "")
        cur.execute(
            "UPDATE doctors SET availability=? WHERE id=?",
            (availability_text, doctor["id"])
        )
        conn.commit()

        flash("Availability updated.", "success")
        return redirect(url_for("doctor.update_availability"))

    #Give the upcoming 7-day date list
    start = datetime.utcnow().date()
    next_dates = [(start + timedelta(days=i)).isoformat() for i in range(7)]

    return render_template(
        "doctor/availability.html",
        doctor=doctor,
        next_seven=next_dates
    )

# It gives a doctor’s patient list
@doctor_blueprint.route("/patients")
@doctor_required
def doctor_patients():
    doctor = get_logged_in_doctor()

    if not doctor:
        flash("Doctor profile missing.", "error")
        return redirect("/login")

    conn = start_connection()
    cur = conn.cursor()

    # Fetch unique patients who had an appointment with this doctor
    cur.execute("""
        SELECT DISTINCT p.id, p.name, p.age, p.gender, p.contact
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = ?
        ORDER BY p.name ASC
    """, (doctor["id"],))

    patients = cur.fetchall()

    return render_template(
        "doctor/patients.html",
        doctor=doctor,
        patients=patients
    )


# View medical history of a specific patient (Doctor side)
@doctor_blueprint.route("/patient-history/<int:patient_id>")
@doctor_required
def patient_history(patient_id):
    doctor = get_logged_in_doctor()
    if not doctor:
        flash("Doctor profile missing.", "error")
        return redirect("/login")

    conn = start_connection()
    cur = conn.cursor()

    # fetch patient details
    cur.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
    patient = cur.fetchone()

    if not patient:
        flash("Patient not found", "error")
        return redirect(url_for("doctor.patients"))

    # fetch treatment + appointment history for this doctor & patient
    cur.execute("""
        SELECT a.date AS visit_date,
               a.time AS visit_time,
               t.diagnosis,
               t.prescription,
               t.notes,
               d.name AS doctor_name
        FROM appointments a
        LEFT JOIN treatments t ON a.id = t.appointment_id
        LEFT JOIN doctors d ON a.doctor_id = d.id
        WHERE a.patient_id = ?
          AND a.doctor_id = ?
        ORDER BY a.date DESC, a.time DESC
    """, (patient_id, doctor["id"]))

    histories = cur.fetchall()

    return render_template(
        "doctor/patient_history.html",
        patient=patient,
        histories=histories
    )
