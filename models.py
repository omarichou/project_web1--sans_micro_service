from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'clients'
    id_client = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    commandes = db.relationship('Commande', backref='client', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Serveur(db.Model):
    __tablename__ = 'serveurs'
    id_serveur = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    commandes = db.relationship('Commande', backref='serveur', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Plat(db.Model):
    __tablename__ = 'plats'
    id_plat = db.Column(db.Integer, primary_key=True)
    nom_plat = db.Column(db.String(100), nullable=False)
    prix_vente = db.Column(db.Numeric(10, 2), nullable=False)
    cout_achat = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50))
    details_commandes = db.relationship('DetailCommande', backref='plat', lazy=True)

class Stock(db.Model):
    __tablename__ = 'stocks'
    id_produit = db.Column(db.Integer, primary_key=True)
    nom_produit = db.Column(db.String(100), nullable=False)
    quantite_dispo = db.Column(db.Integer, nullable=False)
    seuil_alerte = db.Column(db.Integer, nullable=False)
    
    def is_below_threshold(self):
        return self.quantite_dispo <= self.seuil_alerte

class Commande(db.Model):
    __tablename__ = 'commandes'
    id_commande = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_client = db.Column(db.Integer, db.ForeignKey('clients.id_client'), nullable=False)
    id_serveur = db.Column(db.Integer, db.ForeignKey('serveurs.id_serveur'), nullable=False)
    statut = db.Column(db.String(20), nullable=False, default='en_attente')
    details = db.relationship('DetailCommande', backref='commande', lazy=True)
    facture = db.relationship('Facture', backref='commande', uselist=False, lazy=True)

class DetailCommande(db.Model):
    __tablename__ = 'details_commande'
    id = db.Column(db.Integer, primary_key=True)
    id_commande = db.Column(db.Integer, db.ForeignKey('commandes.id_commande'), nullable=False)
    id_plat = db.Column(db.Integer, db.ForeignKey('plats.id_plat'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)

class Facture(db.Model):
    __tablename__ = 'factures'
    id_facture = db.Column(db.Integer, primary_key=True)
    id_commande = db.Column(db.Integer, db.ForeignKey('commandes.id_commande'), unique=True, nullable=False)
    montant = db.Column(db.Numeric(10, 2), nullable=False)
    taxe = db.Column(db.Numeric(10, 2), nullable=False)
    pourboire = db.Column(db.Numeric(10, 2), default=0)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    
    
    # Compatibility English models expected by app.py
    # These are thin copies of the models used previously in app.py so the
    # application can import models from this single file.


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    dishes = db.relationship('Dish', backref='category', lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Dish(db.Model):
    __tablename__ = 'dishes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    def __repr__(self):
        return f"<Dish {self.name} - {self.price}>"


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f"<Order {self.id} user={self.user_id} total={self.total_amount}>"


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    dish = db.relationship('Dish')

    def __repr__(self):
        return f"<OrderItem order={self.order_id} dish={self.dish_id} qty={self.quantity}>"