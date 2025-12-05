"""
admin.py
Admin-only routes:
- Admin dashboard
- Sales summary
- Best / worst seller
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from db import get_connection

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# HELPER: CHECK ADMIN
def _require_admin():
    """
    Simple helper to check if current user is an admin.
    Returns True if admin, otherwise redirects.
    """
    user_type = session.get("user_type")
    if user_type != "Admin":
        flash("Admin access required.")
        return False
    return True


# Adim dashboard
@admin_bp.route("/", methods=["GET"])
def dashboard():
    """
    Shows the main admin dashboard with:
    - total revenue
    - number of orders
    - total items sold
    - best seller potion
    - worst seller potion (based on items sold)
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    conn = get_connection()
    cur = conn.cursor()

    # 1) Total revenue & number of orders
    cur.execute("""
        SELECT
            COUNT(*) AS order_count,
            COALESCE(SUM(Total), 0) AS total_revenue
        FROM Bill_T
    """)
    row = cur.fetchone()
    order_count = row["order_count"]
    total_revenue = float(row["total_revenue"])

    # 2) Total items sold (count BillInventoryItem rows)
    cur.execute("""
        SELECT COUNT(*) AS items_sold
        FROM BillInventoryItem_T
    """)
    row = cur.fetchone()
    items_sold = row["items_sold"]

    # 3) Best seller potion: most sold item
    cur.execute("""
        SELECT
            i.ItemID,
            i.PotionName,
            COUNT(*) AS sold_count
        FROM BillInventoryItem_T bi
        JOIN Inventory_T i ON bi.ItemID = i.ItemID
        GROUP BY i.ItemID, i.PotionName
        ORDER BY sold_count DESC
        LIMIT 1
    """)
    best_seller_row = cur.fetchone()
    if best_seller_row:
        best_seller = {
            "item_id": best_seller_row["ItemID"],
            "name": best_seller_row["PotionName"],
            "sold_count": best_seller_row["sold_count"],
        }
    else:
        best_seller = None

    # 4) Worst seller potion: least sold (but at least 1 sale)
    cur.execute("""
        SELECT
            i.ItemID,
            i.PotionName,
            COUNT(*) AS sold_count
        FROM BillInventoryItem_T bi
        JOIN Inventory_T i ON bi.ItemID = i.ItemID
        GROUP BY i.ItemID, i.PotionName
        HAVING sold_count > 0
        ORDER BY sold_count ASC
        LIMIT 1
    """)
    worst_seller_row = cur.fetchone()
    if worst_seller_row:
        worst_seller = {
            "item_id": worst_seller_row["ItemID"],
            "name": worst_seller_row["PotionName"],
            "sold_count": worst_seller_row["sold_count"],
        }
    else:
        worst_seller = None

    conn.close()

    return render_template(
        "admin_dashboard.html",
        order_count=order_count,
        total_revenue=total_revenue,
        items_sold=items_sold,
        best_seller=best_seller,
        worst_seller=worst_seller,
    )
