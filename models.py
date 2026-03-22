from database import start_connection

def table_creation():
    conn = start_connection()
    cursor = conn.cursor()

    #User Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('admin', 'doctor', 'patient'))
        );
    """)

    #Departments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        );
    """)

    #Doctors Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            specialization TEXT,
            department_id INTEGER,
            contact TEXT,
            availability TEXT,
            user_ref INTEGER UNIQUE,
            FOREIGN KEY (user_ref) REFERENCES users(id),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );
    """)

    #Patients Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            contact TEXT,
            user_ref INTEGER UNIQUE,
            FOREIGN KEY (user_ref) REFERENCES users(id)
        );
    """)

    #Appointments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            date TEXT,
            time TEXT,
            status TEXT CHECK(status IN ('Booked', 'Completed', 'Cancelled')),
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );
    """)

    #Treatments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            diagnosis TEXT,
            prescription TEXT,
            notes TEXT,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        );
    """)

    conn.commit()
