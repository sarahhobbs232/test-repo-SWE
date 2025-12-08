"""
cart.py
Handles:
- Viewing items in the current user's cart
- Removing items from the cart
- Showing subtotal, tax, and total
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection  # uses EternalElixers.db

cart_bp = Blueprint("cart", __name__)

TAX_RATE = 0.06  # 6% sales tax


# View Cart
@cart_bp.route("/cart", methods=["GET"])
def view_cart():
    """
    Shows all items in the current user's cart.
    Calculates subtotal, tax, and total.
    """
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your cart.")
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cur = conn.cursor()

    # Join ShoppingCart_T with Inventory_T to get potion details
    sql = """
        SELECT
            sc.ShoppingCartID,
            sc.ItemID,
            i.PotionName,
            i.PotionDescription,
            i.PotionCost
        FROM ShoppingCart_T sc
        JOIN Inventory_T i ON sc.ItemID = i.ItemID
        WHERE sc.UserID = ?
    """
    cur.execute(sql, (user_id,))
    rows = cur.fetchall()
    conn.close()

    # Convert to a Python list and compute subtotal
    items = []
    subtotal = 0.0

    for row in rows:
        item_dict = {
            "cart_id": row["ShoppingCartID"],
            "item_id": row["ItemID"],
            "name": row["PotionName"],
            "description": row["PotionDescription"],
            "price": row["PotionCost"],
        }
        items.append(item_dict)
        subtotal += float(row["PotionCost"])

    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax, 2)

    return render_template(
        "cart.html",
        items=items,
        subtotal=subtotal,
        tax=tax,
        total=total,
    )


# Remove item from cart
@cart_bp.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    """
    Removes a single item from the current user's cart
    using ShoppingCartID.
    """
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to modify your cart.")
        return redirect(url_for("auth.login"))

    cart_id = request.form.get("cart_id", "").strip()
    if not cart_id:
        flash("Invalid cart item.")
        return redirect(url_for("cart.view_cart"))

    conn = get_connection()
    cur = conn.cursor()

    # Only delete if the cart row belongs to this user
    delete_sql = """
        DELETE FROM ShoppingCart_T
        WHERE ShoppingCartID = ? AND UserID = ?
    """
    cur.execute(delete_sql, (cart_id, user_id))
    conn.commit()
    conn.close()

    flash("Item removed from your cart.")
    return redirect(url_for("cart.view_cart"))

