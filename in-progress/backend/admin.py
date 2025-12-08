"""
admin.py
Admin-only routes:
- Admin dashboard
- Sales report (list of sales per bill)
- CSV export of sales report
- Inventory management (view/add/delete)
- User management (promote user to admin)
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, Response

from db import get_connection, get_all_inventory, add_inventory_item, delete_inventory_item, get_all_users, promote_user_to_admin
import csv
import io

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# HELPER: CHECK ADMIN <<<<<<<<<<
def _require_admin():
    """
    Simple helper to check if current user is an admin.
    Returns True if admin, otherwise False.
    Callers handle redirects.
    """
    user_type = session.get("user_type")
    if user_type != "Admin":
        flash("Admin access required.")
        return False
    return True


# ADMIN DASHBOARD (STATS) <<<<<<<<<<
@admin_bp.route("/", methods=["GET"])
def dashboard():
    """
    Shows the main admin dashboard with:
    - total revenue
    - number of orders
    - total items sold
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    conn = get_connection()
    cur = conn.cursor()

    # 1) Total revenue & number of orders
    cur.execute(
        """
        SELECT
            COUNT(*) AS order_count,
            COALESCE(SUM(Total), 0) AS total_revenue
        FROM Bill_T
        """
    )
    row = cur.fetchone()
    order_count = row["order_count"]
    total_revenue = float(row["total_revenue"])

    # 2) Total items sold (count rows in BillInventoryItem_T)
    cur.execute(
        """
        SELECT COUNT(*) AS items_sold
        FROM BillInventoryItem_T
        """
    )
    row = cur.fetchone()
    items_sold = row["items_sold"]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        order_count=order_count,
        total_revenue=total_revenue,
        items_sold=items_sold,
    )


# SALES REPORT (LIST OF SALES) <<<<<<<<<<
@admin_bp.route("/sales-report", methods=["GET"])
def sales_report():
    """
    Shows a list of all sales (bills), including:
    - BillID
    - date + time
    - username / customer name
    - subtotal, tax, shipping, total
    - item_count (how many items in that bill)
    NOTE: Bill_T.SalesTax is stored as a rate (0.06), so we compute tax_amount here.
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    conn = get_connection()
    cur = conn.cursor()

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
            u.Username,
            u.Name,
            (
                SELECT COUNT(*)
                FROM BillInventoryItem_T bi
                WHERE bi.BillID = b.BillID
            ) AS ItemCount
        FROM Bill_T b
        JOIN User_T u ON b.UserID = u.UserID
        ORDER BY b.SalesDate DESC, b.SaleTime DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    sales = []
    for row in rows:
        subtotal_val = float(row["SubTotal"])
        tax_rate = float(row["SalesTax"])  # e.g. 0.06
        tax_amount = round(subtotal_val * tax_rate, 2)

        sales.append(
            {
                "bill_id": row["BillID"],
                "date": row["SalesDate"],
                "time": row["SaleTime"],
                "username": row["Username"],
                "name": row["Name"],
                "subtotal": subtotal_val,
                "tax": tax_amount,  # <- this is now the dollar amount
                "shipping": float(row["ShippingCost"]),
                "total": float(row["Total"]),
                "item_count": row["ItemCount"],
            }
        )

    return render_template("sales_report.html", sales=sales)


@admin_bp.route("/sales-report/export", methods=["GET"])
def sales_report_export_csv():
    """
    Exports the sales report to CSV.
    Columns:
    BillID, Date, Time, Username, Name, ItemCount, Subtotal, Tax, Shipping, Total
    NOTE: Tax column is the dollar amount (SubTotal * SalesTax), not just the rate.
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    conn = get_connection()
    cur = conn.cursor()

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
            u.Username,
            u.Name,
            (
                SELECT COUNT(*)
                FROM BillInventoryItem_T bi
                WHERE bi.BillID = b.BillID
            ) AS ItemCount
        FROM Bill_T b
        JOIN User_T u ON b.UserID = u.UserID
        ORDER BY b.SalesDate DESC, b.SaleTime DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(
        [
            "BillID",
            "Date",
            "Time",
            "Username",
            "Name",
            "ItemCount",
            "Subtotal",
            "Tax",
            "Shipping",
            "Total",
        ]
    )

    # Data rows
    for row in rows:
        subtotal_val = float(row["SubTotal"])
        tax_rate = float(row["SalesTax"])
        tax_amount = round(subtotal_val * tax_rate, 2)

        writer.writerow(
            [
                row["BillID"],
                row["SalesDate"],
                row["SaleTime"],
                row["Username"],
                row["Name"],
                row["ItemCount"],
                subtotal_val,
                tax_amount,
                float(row["ShippingCost"]),
                float(row["Total"]),
            ]
        )

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sales_report.csv"},
    )


# INVENTORY MANAGEMENT <<<<<<<<<<
@admin_bp.route("/inventory", methods=["GET"])
def inventory_admin():
    """
    Shows all inventory items with options to add/delete.
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    items = get_all_inventory()
    return render_template("admin_inventory.html", items=items)


@admin_bp.route("/inventory/add", methods=["POST"])
def inventory_add():
    """
    Handles form submission for adding a new potion to inventory.
    Expects form fields:
      - name
      - category
      - description
      - cost
      - photo
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    cost_raw = request.form.get("cost", "").strip()
    photo = request.form.get("photo", "").strip()

    # Basic validation
    try:
        cost = float(cost_raw)
    except ValueError:
        cost = -1

    if not name or cost <= 0:
        flash("Name and a positive cost are required to add a potion.")
        return redirect(url_for("admin.inventory_admin"))

    add_inventory_item(name, category, description, cost, photo)
    flash("Potion added to inventory.")
    return redirect(url_for("admin.inventory_admin"))


@admin_bp.route("/inventory/delete/<int:item_id>", methods=["POST"])
def inventory_delete(item_id):
    """
    Deletes an inventory item by ItemID.
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    delete_inventory_item(item_id)
    flash("Potion removed from inventory.")
    return redirect(url_for("admin.inventory_admin"))


# USER MANAGEMENT (PROMOTE TO ADMIN) <<<<<<<<<<
@admin_bp.route("/users", methods=["GET"])
def manage_users():
    """
    Shows all users so an admin can see who is Admin/User
    and promote regular users.
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    users = get_all_users()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/users/promote/<int:user_id>", methods=["POST"])
def promote_user(user_id):
    """
    Promote a regular user to Admin.
    """
    if not _require_admin():
        return redirect(url_for("shop.shop_home"))

    promote_user_to_admin(user_id)
    flash("User promoted to admin.")
    return redirect(url_for("admin.manage_users"))
