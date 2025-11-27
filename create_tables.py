from app import app, db, User, Category, Dish, Order, OrderItem

# with app.app_context():
#     #pour cree tout les tableaux
#     db.create_all()
#     print("Tables créées avec succès!")
    
# with app.app_context():
#     # Ajouter des catégories
#     categories_data = [
#         {'name': 'Plats Principaux'},
#         {'name': 'Desserts'},
#         {'name': 'Boissons'},
#         {'name': 'Pizzas'},
#         {'name': 'Salades'}
#     ]
    
#     for cat_data in categories_data:
#         category = Category(name=cat_data['name'])
#         db.session.add(category)
    
#     db.session.commit()
#     print("Catégories ajoutées!")    
    
    
with app.app_context():

    print("Utilisateurs:", User.query.all())
    print("Catégories:", Category.query.all())
    print("Plats:", Dish.query.all())
    