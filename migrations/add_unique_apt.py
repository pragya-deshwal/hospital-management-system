# migrations/add_unique_index_apt.py
import sqlite3

db = "hospital_system.db"

def add_index():
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # Create unique index to prevent duplicate (doctor_id, date, time) combos
    try:
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_doctor_date_time
            ON appointments(doctor_id, date, time)
        """)
        conn.commit()
        print("Unique index idx_doctor_date_time created (or already exists).")
    except Exception as e:
        print("Failed to create index:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    add_index()
