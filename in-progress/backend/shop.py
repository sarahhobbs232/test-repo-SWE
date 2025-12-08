"""
shop.py
Handles the main shop/home page:
- Showing inventory
- Searching and filtering potions
- Adding items to the cart
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection  # uses EternalElixers.db

# Blueprint for shop-related routes
shop_bp = Blueprint("shop", __name__)


# SHOP HOME / INVENTORY <<<<<<<<<<
@shop_bp.route("/shop", methods=["GET"])
def shop_home():
    """
    Shows the shop page with all available potions.
    Supports:
    - ?q=keyword to search by name/description
    - ?category=Elemental to filter by category

    Only shows inventory that has NOT been sold yet,
    sorted by price (highest to lowest).
    """
    search_term = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_connection()
    cur = conn.cursor()

    # Base query: only unsold items
    sql = """
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
    """
    params = []

    # Add search filter if provided
    if search_term:
        sql += " AND (i.PotionName LIKE ? OR i.PotionDescription LIKE ?)"
        like_pattern = f"%{search_term}%"
        params.extend([like_pattern, like_pattern])

    # Add category filter if provided
    if category:
        sql += " AND i.PotionCategory = ?"
        params.append(category)

    # Sort by price descending (highest -> lowest) per spec
    sql += " ORDER BY i.PotionCost DESC"

    cur.execute(sql, params)
    items = cur.fetchall()
    conn.close()

    # Pass items and filter info to the template
    return render_template(
        "home.html",
        items=items,
        current_search=search_term,
        current_category=category,
    )


# ADD ITEM TO CART <<<<<<<<<<
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
    cur.execute(
        "SELECT PotionName FROM Inventory_T WHERE ItemID = ?",
        (item_id,),
    )
    row = cur.fetchone()
    if row is None:
        conn.close()
        flash("That potion is no longer available.")
        return redirect(url_for("shop.shop_home"))

    potion_name = row["PotionName"]

    # 1.5) Ensure the item has NOT already been sold
    cur.execute(
        """
        SELECT 1
        FROM BillInventoryItem_T
        WHERE ItemID = ?
        """,
        (item_id,),
    )
    sold_row = cur.fetchone()
    if sold_row:
        conn.close()
        flash(f"{potion_name} has already been sold.")
        return redirect(url_for("shop.shop_home"))

    # 2) Prevent duplicates in THIS user's cart
    cur.execute(
        """
        SELECT 1
        FROM ShoppingCart_T
        WHERE UserID = ? AND ItemID = ?
        """,
        (user_id, item_id),
    )
    already_in_cart = cur.fetchone()
    if already_in_cart:
        conn.close()
        flash(f"{potion_name} is already in your cart.")
        return redirect(url_for("cart.view_cart"))

    # 3) Get next ShoppingCartID (MAX + 1)
    cur.execute(
        "SELECT COALESCE(MAX(ShoppingCartID), 0) + 1 AS NextID FROM ShoppingCart_T"
    )
    next_id = cur.fetchone()["NextID"]

    # 4) Insert into ShoppingCart_T
    insert_sql = """
        INSERT INTO ShoppingCart_T (ShoppingCartID, UserID, ItemID)
        VALUES (?, ?, ?)
    """
    cur.execute(insert_sql, (next_id, user_id, item_id))
    conn.commit()
    conn.close()

    flash(f"Added {potion_name} to your cart.")
    return redirect(url_for("shop.shop_home"))
