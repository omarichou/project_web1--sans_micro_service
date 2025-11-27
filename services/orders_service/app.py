from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json

app = Flask(__name__)
DB_PATH = os.environ.get("ORDERS_DATABASE_URL", "sqlite:///orders.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    items = db.Column(db.Text, nullable=False)  # store JSON list of {dish_id, quantity}
    status = db.Column(db.String(40), default="new")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "orders"})


@app.route("/orders", methods=["GET"])
def list_orders():
    user_id = request.args.get('user_id')
    query = Order.query
    if user_id:
        try:
            uid = int(user_id)
            query = query.filter(Order.user_id == uid)
        except ValueError:
            pass
    orders = query.all()
    result = []
    for o in orders:
        result.append({"id": o.id, "user_id": o.user_id, "items": json.loads(o.items), "status": o.status})
    return jsonify(result)


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    items = data.get("items")
    if not user_id or not items:
        return jsonify({"error": "user_id and items required"}), 400
    order = Order(user_id=int(user_id), items=json.dumps(items))
    db.session.add(order)
    db.session.commit()
    return jsonify({"id": order.id, "status": order.status}), 201


def create_db():
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    create_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5003)))
