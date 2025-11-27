from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
DB_PATH = os.environ.get("AUTH_DATABASE_URL", "sqlite:///auth.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # stored as hash


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "auth"})


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "user exists"}), 409
    pw_hash = generate_password_hash(password)
    user = User(username=username, password=pw_hash)
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "username": user.username}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "invalid credentials"}), 401
    # For a real system, return JWT or session token (omitted for scaffold)
    return jsonify({"id": user.id, "username": user.username})


@app.route("/users", methods=["GET"])
def list_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username} for u in users])


def create_db():
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    create_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
