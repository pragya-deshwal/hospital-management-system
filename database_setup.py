from flask import Flask
from models import table_creation
from database import start_connection

app = Flask(__name__)

with app.app_context():
    table_creation()
    conn = start_connection()
    cursor = conn.cursor()

    # Check if admin already exists
    cursor.execute("SELECT * FROM users WHERE role ='admin'")
    admin = cursor.fetchone()

    # If no admin exists, create one
    if admin is None:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )
        conn.commit()
        print("Default admin created: username = admin, password = admin123")

    print("Database initialized successfully!")
