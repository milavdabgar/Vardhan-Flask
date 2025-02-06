from app import create_app, db
from app.models import User

def create_test_users():
    app = create_app()
    with app.app_context():
        # Create a technician
        tech = User.query.filter_by(email='tech@vardhaninsys.com').first()
        if tech is None:
            tech = User(
                email='tech@vardhaninsys.com',
                role='technician',
                full_name='Test Technician',
                contact_number='9876543210',
                is_active=True
            )
            tech.set_password('tech123')
            db.session.add(tech)
            print('Technician user created successfully!')

        # Create a college admin
        college = User.query.filter_by(email='college@example.com').first()
        if college is None:
            college = User(
                email='college@example.com',
                role='college_admin',
                full_name='Test College Admin',
                contact_number='9876543211',
                institution='Test College',
                is_active=True
            )
            college.set_password('college123')
            db.session.add(college)
            print('College admin user created successfully!')

        db.session.commit()

if __name__ == '__main__':
    create_test_users()
