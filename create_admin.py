from app import app, db, User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            email='admin@example.com',
            name='Admin User',
            department='Admin',
            section='A',
            registration_number='ADMIN001',
            year=1,
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created admin user with:")
        print("Email: admin@example.com")
        print("Password: admin123")

if __name__ == '__main__':
    create_admin() 