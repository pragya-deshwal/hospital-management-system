import sqlite3
from flask import g

db = "hospital_system.db"

def start_connection():     #If connection does not exist, create a new one
    conn = getattr(g, "db_connection", None)

    if conn is None:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        g.db_connection = conn

    return g.db_connection


def close_connection(error=None):
    conn = getattr(g, "db_connection", None)

    if conn is not None:
        conn.close()
    