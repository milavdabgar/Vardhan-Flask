import os
import tempfile
from app import create_app, db
from app.models import User, ServiceRequest, RequestFeedback, TechnicianAssignment
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def test_workflow():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the application to use the temporary database
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key'
    })

    with app.app_context():
        # Initialize database
        db.create_all()

        # Create test users
        college_admin = User(
            email='college1@example.com',
            password_hash=generate_password_hash('password123'),
            role='COLLEGE_ADMIN',
            institution='Engineering College',
            full_name='Test College Admin'
        )
        
        technician = User(
            email='jrtech1@example.com',
            password_hash=generate_password_hash('password123'),
            role='JUNIOR_TECHNICIAN',
            institution='Engineering College',
            full_name='Test Junior Technician'
        )

        db.session.add(college_admin)
        db.session.add(technician)
        db.session.commit()

        # Create a service request
        service_request = ServiceRequest(
            title="Test Computer Not Working",
            description="Computer in Lab 101 is not turning on",
            equipment_type="computer",
            priority="high",
            institution=college_admin.institution,
            created_by=college_admin.id,
            status='NEW',
            created_at=datetime.utcnow(),
            ticket_number='SR-TEST001'
        )
        
        db.session.add(service_request)
        db.session.commit()

        # Assign technician
        service_request.assigned_to = technician.id
        service_request.status = 'ASSIGNED'
        db.session.commit()

        # Add feedback
        feedback = RequestFeedback(
            service_request_id=service_request.id,
            rating=5,
            comments="Issue resolved - replaced power supply",
            created_by=technician.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(feedback)
        service_request.status = 'COMPLETED'
        db.session.commit()

        # Verify the workflow
        assert User.query.count() == 2, "Should have 2 users"
        assert ServiceRequest.query.count() == 1, "Should have 1 service request"
        assert RequestFeedback.query.count() == 1, "Should have 1 feedback"
        assert service_request.status == 'COMPLETED', "Service request should be completed"

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

if __name__ == "__main__":
    test_workflow()
