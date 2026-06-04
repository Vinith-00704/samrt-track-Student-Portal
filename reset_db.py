from app import app, db, create_sample_courses

def reset_database():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Creating sample courses...")
        create_sample_courses()
        print("Database reset complete!")

if __name__ == '__main__':
    reset_database() 