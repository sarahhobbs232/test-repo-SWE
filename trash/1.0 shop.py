"""
shop.py
Handles the main shop/home page:
- Showing inventory
- Searching and filtering potions
- Adding items to the cart
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection  # uses your DB helper

# Blueprint for shop-related routes
shop_bp = Blueprint("shop", __name__)


# ------------- SHOP HOME / INVENTORY ------------- #
@shop_bp.route("/shop", methods=["GET"])
def shop_home():
    """
    Shows the shop page with all potions.
    Supports:
    - ?q=keyword to search by name/description
    - ?category=Elemental to filter by category
    """
    search_term = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_connection()
    cur = conn.cursor()

    # Base query
    sql = """
        SELECT ItemID, PotionName, PotionCategory, PotionDescription, PotionCost, PotionPhoto
        FROM Inventory_T
        WHERE 1 = 1
    """
    params = []

    # Add search filter if provided
    if search_term:
        sql += " AND (PotionName LIKE ? OR PotionDescription LIKE ?)"
        like_pattern = f"%{search_term}%"
        params.extend([like_pattern, like_pattern])

    # Add category filter if provided
    if category:
        sql += " AND PotionCategory = ?"
        params.append(category)

    # Optionally add ORDER BY
    sql += " ORDER BY PotionName ASC"

    cur.execute(sql, params)
    items = cur.fetchall()
    conn.close()

    # Pass items and filter info to the template
    return render_template(
        "shop.html",
        items=items,
        current_search=search_term,
        current_category=category,
    )


# Add item to cart
@shop_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    """
    Adds a selected item to the logged-in user's cart.
    Requires:
    - user logged in (session["user_id"])
    - form field "item_id"
    """
    # Require login
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in before adding items to your cart.")
        return redirect(url_for("auth.login"))

    item_id = request.form.get("item_id", "").strip()

    if not item_id:
        flash("Invalid item selection.")
        return redirect(url_for("shop.shop_home"))

    conn = get_connection()
    cur = conn.cursor()

    # 1) Check that the item actually exists
    cur.execute("SELECT PotionName FROM Inventory_T WHERE ItemID = ?", (item_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        flash("That potion does not exist.")
        return redirect(url_for("shop.shop_home"))

    potion_name = row["PotionName"]

    # 2) Get next ShoppingCartID (MAX + 1)
    cur.execute("SELECT COALESCE(MAX(ShoppingCartID), 0) + 1 AS NextID FROM ShoppingCart_T")
    next_id = cur.fetchone()["NextID"]

    # 3) Insert into ShoppingCart_T
    insert_sql = """
        INSERT INTO ShoppingCart_T (ShoppingCartID, UserID, ItemID)
        VALUES (?, ?, ?)
    """
    cur.execute(insert_sql, (next_id, user_id, item_id))
    conn.commit()
    conn.close()

    flash(f"Added {potion_name} to your cart.")
    return redirect(url_for("shop.shop_home"))
