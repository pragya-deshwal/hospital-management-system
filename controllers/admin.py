from flask import Blueprint, render_template, request, redirect, session, flash
from database import start_connection
from functools import wraps

admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")


#Allows access only if the logged-in user is an admin

def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Cannot access! Unauthorized user! Admin login required.", "error")
            return redirect("/login")
        return route_function(*args, **kwargs)

    return wrapper

#Admin Dashboard
@admin_blueprint.route("/dashboard")
@admin_required
def dashboard():
    conn = start_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM doctors")
    doctor_count = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM patients")
    patient_count = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM appointments")
    appointment_count = cur.fetchone()["total"]

    return render_template(
        "admin/dashboard.html",
        doctor_count=doctor_count,
        patient_count=patient_count,
        appointment_count=appointment_count
    )


#Add Doctor
@admin_blueprint.route("/doctors/add", methods=["GET", "POST"])
@admin_required
def add_doctor():
    conn = start_connection()
    cur = conn.cursor()

    # Load department list
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()

    if request.method == "POST":
        name = request.form["name"]
        specialization = request.form["specialization"]
        availability = request.form["availability"]
        username = request.form["username"]
        password = request.form["password"]
        department_id = request.form["department_id"]
        contact = request.form.get("contact", "")

        # 1. Create user for doctor
        try:
            cur.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, 'doctor')
            """, (username, password))
            conn.commit()
        except:
            flash("Username already taken! Please choose another.", "error")
            return redirect("/admin/doctors/add")

        # 2. Get new user's ID
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        user_ref = cur.fetchone()["id"]

        # 3. Insert doctor details
        cur.execute("""
            INSERT INTO doctors (name, specialization, department_id, contact, availability, user_ref)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, specialization, department_id, contact, availability, user_ref))
        conn.commit()

        flash("Doctor has been added successfully.", "success")
        return redirect("/admin/doctors")

    return render_template("admin/add_doctor.html", departments=departments)



#Allows us to view all the doctors
@admin_blueprint.route("/doctors")
@admin_required
def doctors_list():
    conn = start_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM doctors")
    doctors = cur.fetchall()

    return render_template("admin/doctors_list.html", doctors=doctors)


#Allows editing doctor's information
@admin_blueprint.route("/doctors/edit/<int:doctor_id>", methods=["GET", "POST"])
@admin_required
def edit_doctor(doctor_id):
    conn = start_connection()
    cur = conn.cursor()

    #Fetch deatils of the doctors that already exist
    cur.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,))
    doctor = cur.fetchone()

    if request.method == "POST":
        updated_name = request.form["name"]
        updated_specialization = request.form["specialization"]
        updated_availability = request.form["availability"]

        cur.execute("""
            UPDATE doctors
            SET name=?, specialization=?, availability=?
            WHERE id=?
        """, (updated_name, updated_specialization, updated_availability, doctor_id))
        conn.commit()

        flash("Doctor information updated successfully.", "success")
        return redirect("/admin/doctors")

    return render_template("admin/edit_doctor.html", doctor=doctor)


#Allows us to delete a doctor
@admin_blueprint.route("/doctors/delete/<int:doctor_id>")
@admin_required
def delete_doctor(doctor_id):
    conn = start_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM doctors WHERE id=?", (doctor_id,))
    conn.commit()

    flash("Doctor has been removed.", "success")
    return redirect("/admin/doctors")


#Allows us to view and search patients
@admin_blueprint.route("/patients", methods=["GET", "POST"])
@admin_required
def patients_list():
    conn = start_connection()
    cur = conn.cursor()

    query = "SELECT * FROM patients"
    params = ()

    if request.method == "POST":
        keyword = request.form["search"]
        query = """
            SELECT * FROM patients
            WHERE name LIKE ? OR contact LIKE ? OR id LIKE ?
        """
        params = (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")

    cur.execute(query, params)
    patients = cur.fetchall()

    return render_template("admin/patient_list.html", patients=patients)


#View appointments with patient and doctor details
@admin_blueprint.route("/appointments")
@admin_required
def appointments_list():
    conn = start_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.*, 
               p.name AS patient_name,
               d.name AS doctor_name
        FROM appointments AS a
        JOIN patients AS p ON a.patient_id = p.id
        JOIN doctors  AS d ON a.doctor_id = d.id
        ORDER BY a.date, a.time
    """)

    appointments = cur.fetchall()

    return render_template("admin/appointment_list.html", appointments=appointments)

#View patient medical history
@admin_blueprint.route("/patient-history/<int:patient_id>")
@admin_required
def admin_patient_history(patient_id):
    db = start_connection()
    cur = db.cursor()
    cur.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
    patient = cur.fetchone()
    if not patient:
        flash("Patient not found", "error")
        return redirect("/admin/patients")

    cur.execute("""
        SELECT a.id as appointment_id, a.date, a.time, a.status,
               d.name AS doctor_name, t.diagnosis, t.prescription, t.notes
        FROM appointments a
        LEFT JOIN doctors d ON a.doctor_id = d.id
        LEFT JOIN treatments t ON t.appointment_id = a.id
        WHERE a.patient_id = ?
        ORDER BY a.date DESC, a.time DESC
    """, (patient_id,))
    history = cur.fetchall()
    return render_template("admin/patient_history.html", patient=patient, history=history)

