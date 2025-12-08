"""
db.py
- Handles connection to the EternalElixers.db SQLite database
- Initializes schema and provides helper functions for
- inventory management and admin promotion
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "EternalElixers.db"
SCHEMA_PATH = BASE_DIR / "EternalElixers.sql"


def get_connection():
    """
    Opens a connection to the EternalElixers.db SQLite database.
    Returns a connection object that other modules can use.
    Ensures foreign keys are enforced and rows are dict-like.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    If the database file is missing or empty, create it
    and run the schema/seed SQL from EternalElixers.sql
    """
    # If file exists AND is non-empty, leave it alone
    if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        return

    print("Initializing new EternalElixers.db at:", DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    conn.executescript(sql)
    conn.commit()
    conn.close()

    print("Database initialized.")


# INVENTORY HELPERS <<<<<<<<<<
def get_all_inventory():
    """
    Return all *available* inventory items (not yet sold),
    sorted by price from highest to lowest.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT i.ItemID,
               i.PotionName,
               i.PotionCategory,
               i.PotionDescription,
               i.PotionCost,
               i.PotionPhoto
        FROM Inventory_T AS i
        WHERE NOT EXISTS (
            SELECT 1
            FROM BillInventoryItem_T AS bi
            WHERE bi.ItemID = i.ItemID
        )
        ORDER BY i.PotionCost DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def add_inventory_item(name, category, description, cost, photo):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Inventory_T (PotionName, PotionCategory, PotionDescription, PotionCost, PotionPhoto)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, category, description, cost, photo),
    )
    conn.commit()
    conn.close()


def delete_inventory_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Inventory_T WHERE ItemID = ?", (item_id,))
    conn.commit()
    conn.close()


# USER / ADMIN HELPERS <<<<<<<<<<
def get_all_users():
    """
    Return all users for the admin 'manage users' screen.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT UserID, Username, Name, Email, UserType
        FROM User_T
        ORDER BY UserID
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def promote_user_to_admin(user_id):
    """
    Promote a regular user to Admin.
    Called only from an admin-only route.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE User_T
        SET UserType = 'Admin'
        WHERE UserID = ?
        """,
        (user_id,),
    )
    conn.commit()
    conn.close()
