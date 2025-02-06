from app import create_app, db
from app.models import User

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@vardhaninsys.com').first()
        if admin is None:
            admin = User(
                email='admin@vardhaninsys.com',
                role='admin',
                full_name='System Administrator',
                contact_number='1234567890',
                is_active=True
            )
            admin.set_password('admin123')  # Change this password in production
            db.session.add(admin)
            db.session.commit()
            print('Admin user created successfully!')
        else:
            print('Admin user already exists.')

if __name__ == '__main__':
    create_admin_user()
