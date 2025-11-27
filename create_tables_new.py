from app import app, db

def init_db():
    with app.app_context():
        # Supprimer toutes les tables existantes
        db.drop_all()
        # Créer toutes les tables
        db.create_all()
        print("Base de données créée avec succès!")

if __name__ == "__main__":
    init_db()