from flask import Flask, redirect, url_for
from auth import auth_bp
from shop import shop_bp
from cart import cart_bp
from checkout import checkout_bp
from admin import admin_bp
from db import init_db   # import

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_KEY"

# initialize DB once at startup
init_db()

# register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(checkout_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def home():
    return redirect(url_for("shop.shop_home"))

if __name__ == "__main__":
    app.run(debug=True)
