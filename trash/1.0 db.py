# db.py
# Handles connection to the EternalElixers.db SQLite database

import sqlite3
from pathlib import Path

# EternalElixers.db must be in the SAME folder as this file
DB_PATH = Path(__file__).resolve().parent / "EternalElixers.db"

def get_connection():
    """
    Opens a connection to the EternalElixers.db SQLite database.
    Returns a connection object that other modules can use.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access: row["Username"]
    return conn
