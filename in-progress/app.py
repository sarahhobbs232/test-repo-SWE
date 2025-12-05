from flask import Flask, redirect, url_for
from auth import auth_bp
from shop import shop_bp
from cart import cart_bp
from checkout import checkout_bp
from admin import admin_bp

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_KEY"  # Needed for session cookies


# register blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(checkout_bp)
app.register_blueprint(admin_bp)


# default route
@app.route("/")
def home():
    """
    Redirect the user to the shop page.
    """
    return redirect(url_for("shop.shop_home"))


# start flask server
if __name__ == "__main__":
    app.run(debug=True)
