from app import app, db, User, Category, Dish
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        try:
            # Supprime et recrée toutes les tables
            db.drop_all()
            db.create_all()
            print("Tables créées avec succès!")

            # Créer un utilisateur administrateur
            admin = User(
                username='Admin',
                email='admin@restaurant.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            print("Utilisateur admin créé!")

            # Créer les catégories
            categories = [
                Category(name='Entrées'),
                Category(name='Plats principaux'),
                Category(name='Desserts'),
                Category(name='Boissons')
            ]
            db.session.add_all(categories)
            print("Catégories créées!")

            # Pour s'assurer que les catégories sont en base avant d'ajouter les plats
            db.session.flush()

            # Ajouter des plats
            plats = [
                Dish(
                    name='Salade César',
                    description='Salade romaine, poulet grillé, croûtons, parmesan',
                    price=800.00,
                    cost=350.00,
                    category_id=1
                ),
                Dish(
                    name='Couscous Royal',
                    description='Couscous avec agneau, poulet et merguez',
                    price=1500.00,
                    cost=800.00,
                    category_id=2
                ),
                Dish(
                    name='Tarte aux pommes',
                    description='Tarte maison aux pommes caramélisées',
                    price=400.00,
                    cost=150.00,
                    category_id=3
                ),
                Dish(
                    name='Coca-Cola',
                    description='Boisson gazeuse rafraîchissante',
                    price=150.00,
                    cost=40.00,
                    category_id=4
                )
            ]
            db.session.add_all(plats)
            print("Plats ajoutés!")

            # Valider toutes les modifications
            db.session.commit()
            print("Toutes les données ont été initialisées avec succès!")

        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de l'initialisation de la base de données: {str(e)}")

if __name__ == '__main__':
    init_db()