from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DecimalField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from datetime import datetime
from sqlalchemy import text

from models import db, User, Category, Dish, Order, OrderItem

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)


def ensure_missing_columns():
    """Check common migration additions and add columns if they are missing (SQLite safe ALTER TABLE ADD COLUMN).
    This is a small, safe helper for development to avoid forcing a full DB reset.
    """
    with app.app_context():
        try:
            conn = db.engine.connect()

            # helper to get column names for a table (robust to different Row types)
            def get_cols(table_name):
                try:
                    r = conn.execute(text(f"PRAGMA table_info('{table_name}')"))
                except Exception:
                    return []
                cols = []
                for row in r:
                    name = None
                    # Try common access patterns
                    try:
                        name = row._mapping['name']
                    except Exception:
                        try:
                            name = row['name']
                        except Exception:
                            try:
                                name = row[1]
                            except Exception:
                                name = None
                    if name:
                        cols.append(name)
                return cols

            # Try to add dishes.cost if missing
            try:
                cols = get_cols('dishes')
                if 'cost' not in cols and cols:
                    conn.execute(text("ALTER TABLE dishes ADD COLUMN cost NUMERIC"))
                    app.logger.info('Colonne cost ajoutée à dishes')
                    # initialize existing rows to 0
                    try:
                        conn.execute(text("UPDATE dishes SET cost = 0 WHERE cost IS NULL"))
                    except Exception:
                        pass
            except Exception:
                pass

            # users.is_admin and users.created_at
            try:
                cols = get_cols('users')
                if 'is_admin' not in cols and cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                    app.logger.info('Colonne is_admin ajoutée à users')
                if 'created_at' not in cols and cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))
                    app.logger.info('Colonne created_at ajoutée à users')
                    # set created_at for existing rows
                    try:
                        conn.execute(text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
                    except Exception:
                        pass
            except Exception:
                pass

            conn.close()
        except Exception as e:
            app.logger.error(f"Erreur lors de la vérification des colonnes: {str(e)}")
    # Ensure default admin user is flagged (helpful if DB was created without seed)
    try:
        with app.app_context():
            admin_user = User.query.filter_by(email='admin@restaurant.com').first()
            if admin_user and not admin_user.is_admin:
                admin_user.is_admin = True
                db.session.commit()
                app.logger.info('Utilisateur admin existant marqué is_admin=True')
    except Exception:
        # if tables don't exist or commit fails, ignore here
        pass

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class DishForm(FlaskForm):
    name = StringField('Nom du plat', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = DecimalField('Prix (DA)', validators=[DataRequired(), NumberRange(min=0)])
    cost = DecimalField('Coût (DA)', validators=[NumberRange(min=0)], default=0)
    category_id = SelectField('Catégorie', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Ajouter')

class CategoryForm(FlaskForm):
    name = StringField('Nom de la catégorie', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Créer')

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Accès refusé: privilèges administrateur requis.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/')
def index():
    featured_dishes = Dish.query.limit(6).all()
    categories = Category.query.all()
    return render_template('index.html', categories=categories, featured_dishes=featured_dishes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Cet email est déjà utilisé.', 'danger')
        else:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Votre compte a été créé avec succès! Vous pouvez maintenant vous connecter.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('Une erreur est survenue lors de la création de votre compte.', 'danger')
                app.logger.error(f'Erreur lors de l\'inscription : {str(e)}')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = bool(user.is_admin)
            flash('Connexion réussie!', 'success')
            return redirect(url_for('index'))
        flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user = User.query.get_or_404(session['user_id'])
    user_orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('profile.html', user=user, orders=user_orders)

@app.route('/dishes')
def dishes_view():
    category_filter = request.args.get('category', type=int)
    query = Dish.query
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    dishes = query.all()
    categories = Category.query.all()
    return render_template('dishes.html', dishes=dishes, categories=categories, selected_category=category_filter)

@app.route('/add_to_cart/<int:dish_id>', methods=['POST'])
@login_required
def add_to_cart(dish_id):
    try:
        dish = Dish.query.get_or_404(dish_id)
        quantity = int(request.form.get('quantity', 1))
        
        if quantity < 1:
            flash('La quantité doit être supérieure à 0.', 'danger')
            return redirect(url_for('dishes_view'))

        if 'cart' not in session:
            session['cart'] = {}
        
        cart = session['cart']
        str_id = str(dish_id)
        
        if str_id in cart:
            cart[str_id]['quantity'] += quantity
        else:
            cart[str_id] = {
                'quantity': quantity,
                'name': dish.name,
                'price': float(dish.price)
            }
        
        session['cart'] = cart
        flash(f'{quantity} {dish.name} ajouté(s) au panier.', 'success')
        
    except Exception as e:
        flash('Une erreur est survenue lors de l\'ajout au panier.', 'danger')
        app.logger.error(f'Erreur lors de l\'ajout au panier : {str(e)}')
    
    return redirect(url_for('dishes_view'))

@app.route('/cart')
@login_required
def cart():
    if 'cart' not in session or not session['cart']:
        flash('Votre panier est vide.', 'info')
        return redirect(url_for('dishes_view'))

    cart_items = []
    total = 0
    
    try:
        for dish_id, item in session['cart'].items():
            dish = Dish.query.get(int(dish_id))
            if dish:
                subtotal = item['quantity'] * float(dish.price)
                cart_items.append({
                    'dish': dish,
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                })
                total += subtotal
    except Exception as e:
        flash('Une erreur est survenue lors du chargement du panier.', 'danger')
        app.logger.error(f'Erreur lors du chargement du panier : {str(e)}')
        return redirect(url_for('dishes_view'))

    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:dish_id>', methods=['POST'])
@login_required
def update_cart(dish_id):
    if 'cart' not in session:
        return redirect(url_for('cart'))

    cart = session['cart']
    str_id = str(dish_id)
    
    try:
        if str_id in cart:
            action = request.form.get('action')
            if action == 'remove':
                del cart[str_id]
                flash('Article retiré du panier.', 'success')
            elif action == 'update':
                quantity = int(request.form.get('quantity', 1))
                if quantity > 0:
                    cart[str_id]['quantity'] = quantity
                    flash('Quantité mise à jour.', 'success')
                else:
                    del cart[str_id]
                    flash('Article retiré du panier.', 'success')
        
        session['cart'] = cart
        
    except Exception as e:
        flash('Une erreur est survenue lors de la mise à jour du panier.', 'danger')
        app.logger.error(f'Erreur lors de la mise à jour du panier : {str(e)}')

    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Votre panier est vide.', 'warning')
        return redirect(url_for('dishes_view'))

    try:
        # Créer une nouvelle commande
        total_amount = sum(
            item['quantity'] * item['price']
            for item in session['cart'].values()
        )
        
        new_order = Order(
            user_id=session['user_id'],
            status='en attente',
            total_amount=total_amount
        )
        db.session.add(new_order)
        print("Utilisateurs:", Order.query.all())
        # Ajouter les items de la commande
        for dish_id, item in session['cart'].items():
            dish = Dish.query.get(int(dish_id))
            if dish:
                order_item = OrderItem(
                    order=new_order,
                    dish_id=dish.id,
                    quantity=item['quantity'],
                    price=dish.price
                )
                db.session.add(order_item)
        
        db.session.commit()
        session.pop('cart')
        flash('Votre commande a été passée avec succès!', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue lors de la validation de votre commande.', 'danger')
        app.logger.error(f'Erreur lors du checkout : {str(e)}')
        return redirect(url_for('cart'))

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        if Category.query.filter_by(name=form.name.data).first():
            flash('Une catégorie avec ce nom existe déjà.', 'danger')
        else:
            new_category = Category(name=form.name.data)
            try:
                db.session.add(new_category)
                db.session.commit()
                flash('Catégorie créée avec succès!', 'success')
                return redirect(url_for('admin_categories'))
            except Exception as e:
                db.session.rollback()
                flash('Une erreur est survenue lors de la création de la catégorie.', 'danger')
                app.logger.error(f'Erreur lors de la création de catégorie : {str(e)}')
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin_categories.html', form=form, categories=categories)

@app.route('/admin/dishes', methods=['GET', 'POST'])
@admin_required
def admin_dishes():
    form = DishForm()
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        new_dish = Dish(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            cost=(form.cost.data if form.cost.data is not None else 0),
            category_id=form.category_id.data
        )
        try:
            db.session.add(new_dish)
            db.session.commit()
            flash('Plat ajouté avec succès!', 'success')
            return redirect(url_for('admin_dishes'))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'ajout du plat.', 'danger')
            app.logger.error(f'Erreur lors de l\'ajout du plat : {str(e)}')
    
    dishes = Dish.query.join(Category).all()
    return render_template('admin_dishes.html', form=form, dishes=dishes)


@app.route('/admin/orders', methods=['GET', 'POST'])
@admin_required
def admin_orders():
    if request.method == 'POST':
        order_id = request.form.get('order_id', type=int)
        new_status = request.form.get('status')
        if order_id and new_status:
            order = Order.query.get(order_id)
            if order:
                try:
                    order.status = new_status
                    db.session.commit()
                    flash('Statut de la commande mis à jour.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash('Impossible de mettre à jour le statut.', 'danger')
                    app.logger.error(f'Erreur mise à jour statut commande: {str(e)}')
        return redirect(url_for('admin_orders'))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)


@app.route('/admin/stats')
@admin_required
def stats():
    # Chiffres globaux
    total_orders = Order.query.count()
    total_sales = 0
    customers = set()
    try:
        orders = Order.query.all()
        for o in orders:
            total_sales += float(o.total_amount)
            customers.add(o.user_id)

        # Calculer marge approximative: (price - cost) * qty pour chaque order item
        total_margin = 0
        items = OrderItem.query.join(Dish, OrderItem.dish_id == Dish.id).all()
        for it in items:
            dish = Dish.query.get(it.dish_id)
            price = float(it.price)
            cost = float(dish.cost) if dish and dish.cost is not None else 0
            total_margin += (price - cost) * it.quantity

        top_dishes = db.session.query(Dish.name, db.func.sum(OrderItem.quantity).label('sold'))
        top_dishes = top_dishes.join(OrderItem, Dish.id == OrderItem.dish_id)
        top_dishes = top_dishes.group_by(Dish.id).order_by(db.desc('sold')).limit(5).all()

    except Exception as e:
        app.logger.error(f'Erreur calcul statistiques: {str(e)}')
        flash('Impossible de calculer les statistiques.', 'danger')
        total_sales = 0
        total_margin = 0
        top_dishes = []

    return render_template('stats.html', total_orders=total_orders, total_sales=total_sales,
                           customers_count=len(customers), total_margin=total_margin, top_dishes=top_dishes)

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Base de données créée avec succès!")
            # Ensure we add small schema changes to existing DBs (dev helper)
            # ensure_missing_columns()
        except Exception as e:
            print(f"Erreur lors de la création de la base de données: {str(e)}")
    
    app.run(debug=True)