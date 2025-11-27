from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
DB_PATH = os.environ.get("DISHES_DATABASE_URL", "sqlite:///dishes.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category')


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "dishes"})


@app.route("/categories", methods=["GET"])
def list_categories():
    cats = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])


@app.route("/dishes", methods=["GET"])
def list_dishes():
    category = request.args.get('category')
    query = Dish.query
    if category:
        try:
            cid = int(category)
            query = query.filter(Dish.category_id == cid)
        except ValueError:
            # try by name
            query = query.join(Category).filter(Category.name == category)
    dishes = query.all()
    result = []
    for d in dishes:
        cat = None
        if d.category:
            cat = {"id": d.category.id, "name": d.category.name}
        result.append({"id": d.id, "name": d.name, "price": d.price, "category": cat})
    return jsonify(result)


@app.route("/dishes", methods=["POST"])
def create_dish():
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    category = data.get("category")
    if not name or price is None:
        return jsonify({"error": "name and price required"}), 400
    category_obj = None
    if category is not None:
        # accept id or name
        if isinstance(category, int) or (isinstance(category, str) and category.isdigit()):
            category_obj = Category.query.get(int(category))
        else:
            category_obj = Category.query.filter_by(name=category).first()
        if category_obj is None and isinstance(category, str):
            category_obj = Category(name=category)
            db.session.add(category_obj)
            db.session.flush()

    dish = Dish(name=name, price=float(price), category=category_obj)
    db.session.add(dish)
    db.session.commit()
    return jsonify({"id": dish.id, "name": dish.name, "price": dish.price}), 201


def create_db(seed=True):
    with app.app_context():
        db.create_all()
        if seed:
            # add sample categories/dishes if empty
            if Category.query.count() == 0:
                c1 = Category(name='Entrées')
                c2 = Category(name='Plats')
                c3 = Category(name='Desserts')
                db.session.add_all([c1, c2, c3])
                db.session.commit()
            if Dish.query.count() == 0:
                cat_plats = Category.query.filter_by(name='Plats').first()
                cat_desserts = Category.query.filter_by(name='Desserts').first()
                d1 = Dish(name='Salade niçoise', price=8.5, category=cat_plats)
                d2 = Dish(name='Steak frites', price=14.0, category=cat_plats)
                d3 = Dish(name='Crème brûlée', price=6.0, category=cat_desserts)
                db.session.add_all([d1, d2, d3])
                db.session.commit()


if __name__ == "__main__":
    create_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5002)))
