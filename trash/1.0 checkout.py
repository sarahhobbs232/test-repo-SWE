"""
checkout.py
Handles:
- Checkout page (review cart + enter shipping/payment)
- Creating a Bill (Bill_T + BillInventoryItem_T)
- Confirmation page showing order summary
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from db import get_connection

checkout_bp = Blueprint("checkout", __name__)

TAX_RATE = 0.06  # must match what you're using elsewhere


# HELPER: GET CURRENT USER CART ITEMS
def _get_cart_items_for_user(user_id):
    """
    Returns (items, subtotal) for the given user_id.
    Each item is a dict with:
    - cart_id
    - item_id
    - name
    - description
    - price
    """
    conn = get_connection()
    cur = conn.cursor()

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

    items = []
    subtotal = 0.0

    for row in rows:
        item = {
            "cart_id": row["ShoppingCartID"],
            "item_id": row["ItemID"],
            "name": row["PotionName"],
            "description": row["PotionDescription"],
            "price": float(row["PotionCost"]),
        }
        items.append(item)
        subtotal += item["price"]

    return items, subtotal


# Checkout page
@checkout_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    """
    GET: Show checkout form (cart summary + shipping options + address fields)
    POST: Create Bill + BillInventoryItem rows, clear cart, redirect to confirmation
    """
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to checkout.")
        return redirect(url_for("auth.login"))

    # Get current cart items
    items, subtotal = _get_cart_items_for_user(user_id)
    if not items:
        flash("Your cart is empty. Add items before checking out.")
        return redirect(url_for("cart.view_cart"))

    # Load shipping options from Shipping_T
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ShippingID, ShippingType, ShippingCost FROM Shipping_T")
    shipping_rows = cur.fetchall()

    shipping_options = [
        {
            "id": row["ShippingID"],
            "type": row["ShippingType"],
            "cost": float(row["ShippingCost"]),
        }
        for row in shipping_rows
    ]
    conn.close()

    # Default to first shipping option if none selected yet
    if shipping_options:
        default_shipping_id = shipping_options[0]["id"]
    else:
        default_shipping_id = None

    if request.method == "POST":
        # Read form fields
        street = request.form.get("street", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        zip_code = request.form.get("zip", "").strip()
        shipping_id_str = request.form.get("shipping_id", "").strip()

        if not street or not city or not state or not zip_code or not shipping_id_str:
            flash("Please fill out all address and shipping fields.")
            return redirect(url_for("checkout.checkout"))

        shipping_id = int(shipping_id_str)

        # Find selected shipping cost
        selected_shipping = next(
            (s for s in shipping_options if s["id"] == shipping_id),
            None
        )
        if not selected_shipping:
            flash("Invalid shipping option.")
            return redirect(url_for("checkout.checkout"))

        shipping_cost = selected_shipping["cost"]

        # Recalculate totals
        tax = round(subtotal * TAX_RATE, 2)
        total = round(subtotal + tax + shipping_cost, 2)

        # Insert into Bill_T + BillInventoryItem_T and clear cart
        conn = get_connection()
        cur = conn.cursor()

        # 1) Get next BillID
        cur.execute("SELECT COALESCE(MAX(BillID), 0) + 1 AS NextID FROM Bill_T")
        next_bill_id = cur.fetchone()["NextID"]

        # 2) Calculate date/time
        now = datetime.now()
        sales_date = now.strftime("%Y-%m-%d")
        sales_time = now.strftime("%H:%M:%S")

        # Use the first item_id for Bill_T.ItemID
        first_item_id = items[0]["item_id"]

        insert_bill_sql = """
            INSERT INTO Bill_T (
                BillID, UserID, ShoppingCartID, ItemID,
                SalesDate, SaleTime, SalesTax, SubTotal,
                ShippingCost, Total, Street, City, State, Zip, ShippingID
            )
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cur.execute(
            insert_bill_sql,
            (
                next_bill_id,
                user_id,
                first_item_id,
                sales_date,
                sales_time,
                TAX_RATE,
                subtotal,
                shipping_cost,
                total,
                street,
                city,
                state,
                zip_code,
                shipping_id,
            ),
        )

        # 3) Insert each item into BillInventoryItem_T
        cur.execute(
            "SELECT COALESCE(MAX(BillInventoryItemID), 0) + 1 AS NextID FROM BillInventoryItem_T"
        )
        next_bill_item_id = cur.fetchone()["NextID"]

        insert_bill_item_sql = """
            INSERT INTO BillInventoryItem_T (BillInventoryItemID, BillID, ItemID)
            VALUES (?, ?, ?)
        """

        current_id = next_bill_item_id
        for item in items:
            cur.execute(insert_bill_item_sql, (current_id, next_bill_id, item["item_id"]))
            current_id += 1

        # 4) Clear the user's cart
        cur.execute("DELETE FROM ShoppingCart_T WHERE UserID = ?", (user_id,))

        conn.commit()
        conn.close()

        flash("Order placed successfully!")
        return redirect(url_for("checkout.confirmation", bill_id=next_bill_id))

    # If GET, just render the checkout page
    tax = round(subtotal * TAX_RATE, 2)
    # Use default shipping cost just for preview
    preview_shipping_cost = shipping_options[0]["cost"] if shipping_options else 0.0
    preview_total = round(subtotal + tax + preview_shipping_cost, 2)

    return render_template(
        "checkout.html",
        items=items,
        subtotal=subtotal,
        tax=tax,
        shipping_options=shipping_options,
        default_shipping_id=default_shipping_id,
        preview_total=preview_total,
    )


# Confirmation page
@checkout_bp.route("/confirmation/<int:bill_id>", methods=["GET"])
def confirmation(bill_id):
    """
    Shows a simple order confirmation / receipt for the given BillID.
    """
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your orders.")
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cur = conn.cursor()

    # Get Bill info
    cur.execute(
        """
        SELECT
            b.BillID,
            b.SalesDate,
            b.SaleTime,
            b.SubTotal,
            b.SalesTax,
            b.ShippingCost,
            b.Total,
            b.Street,
            b.City,
            b.State,
            b.Zip,
            s.ShippingType
        FROM Bill_T b
        LEFT JOIN Shipping_T s ON b.ShippingID = s.ShippingID
        WHERE b.BillID = ? AND b.UserID = ?
        """,
        (bill_id, user_id),
    )
    bill = cur.fetchone()

    if bill is None:
        conn.close()
        flash("Order not found.")
        return redirect(url_for("shop.shop_home"))

    # Get items for the bill
    cur.execute(
        """
        SELECT
            i.PotionName,
            i.PotionDescription,
            i.PotionCost
        FROM BillInventoryItem_T bi
        JOIN Inventory_T i ON bi.ItemID = i.ItemID
        WHERE bi.BillID = ?
        """,
        (bill_id,),
    )
    item_rows = cur.fetchall()
    conn.close()

    items = [
        {
            "name": row["PotionName"],
            "description": row["PotionDescription"],
            "price": float(row["PotionCost"]),
        }
        for row in item_rows
    ]

    return render_template(
        "confirmation.html",
        bill=bill,
        items=items,
    )
