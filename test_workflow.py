from app import create_app, db
from app.models import User, ServiceRequest, RequestFeedback, TechnicianAssignment
from datetime import datetime, timedelta

def test_workflow():
    app = create_app()
    with app.app_context():
        # 1. Create a service request as college admin
        college_admin = User.query.filter_by(email='college1@example.com').first()
        
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
        
        # Auto-assign to Jr. Technician
        jr_tech = User.query.join(TechnicianAssignment).filter(
            TechnicianAssignment.college == college_admin.institution,
            TechnicianAssignment.is_senior == False
        ).first()
        
        if jr_tech:
            service_request.assigned_to = jr_tech.id
            print(f"\n1. Service Request created and assigned to {jr_tech.full_name}")
        
        db.session.add(service_request)
        db.session.commit()
        
        # 2. Jr. Technician schedules a visit
        service_request.status = 'SCHEDULED'
        service_request.scheduled_date = datetime.utcnow().date()
        service_request.scheduled_time = datetime.utcnow().time()
        service_request.scheduled_at = datetime.utcnow()
        print(f"\n2. Visit scheduled for {service_request.format_schedule_time()}")
        db.session.commit()
        
        # 3. College admin confirms visit
        service_request.status = 'VISITED'
        service_request.visited_at = datetime.utcnow()
        service_request.actual_visit_time = datetime.utcnow()
        service_request.visit_count = 1
        print("\n3. Visit confirmed by college admin")
        db.session.commit()
        
        # 4. Jr. Technician resolves the issue
        service_request.status = 'RESOLVED'
        service_request.resolved_at = datetime.utcnow()
        service_request.resolution_notes = "Replaced faulty power supply"
        service_request.reopen_deadline = datetime.utcnow() + timedelta(days=7)
        print("\n4. Issue resolved by technician")
        db.session.commit()
        
        # 5. College admin reopens the request
        service_request.status = 'REOPENED'
        service_request.reopened_at = datetime.utcnow()
        
        # Auto-assign to Sr. Technician
        sr_tech = User.query.join(TechnicianAssignment).filter(
            TechnicianAssignment.college == college_admin.institution,
            TechnicianAssignment.is_senior == True
        ).first()
        
        if sr_tech:
            service_request.assigned_to = sr_tech.id
            print(f"\n5. Request reopened and assigned to senior technician {sr_tech.full_name}")
        db.session.commit()
        
        # 6. Sr. Technician schedules another visit
        service_request.status = 'SCHEDULED'
        service_request.scheduled_date = datetime.utcnow().date()
        service_request.scheduled_time = datetime.utcnow().time()
        service_request.scheduled_at = datetime.utcnow()
        print(f"\n6. New visit scheduled by senior technician")
        db.session.commit()
        
        # 7. College admin confirms second visit
        service_request.status = 'VISITED'
        service_request.visited_at = datetime.utcnow()
        service_request.actual_visit_time = datetime.utcnow()
        service_request.visit_count += 1
        print("\n7. Second visit confirmed")
        db.session.commit()
        
        # 8. Sr. Technician resolves the issue
        service_request.status = 'RESOLVED'
        service_request.resolved_at = datetime.utcnow()
        service_request.resolution_notes += "\nReplaced motherboard and confirmed system is working"
        service_request.reopen_deadline = datetime.utcnow() + timedelta(days=7)
        print("\n8. Issue resolved by senior technician")
        db.session.commit()
        
        # 9. College admin closes the request with feedback
        service_request.status = 'CLOSED'
        service_request.closed_at = datetime.utcnow()
        
        feedback = RequestFeedback(
            service_request_id=service_request.id,
            rating=5,
            comments="Great service, especially by the senior technician",
            created_by=college_admin.id,
            is_auto_rated=False
        )
        db.session.add(feedback)
        print("\n9. Request closed with 5-star feedback")
        db.session.commit()
        
        print("\nWorkflow test completed successfully!")
        print(f"Service Request Status: {service_request.status}")
        print(f"Total Visits: {service_request.visit_count}")
        print(f"Final Resolution: {service_request.resolution_notes}")
        print(f"Feedback Rating: {feedback.rating} stars")
        print(f"Feedback Comments: {feedback.comments}")

if __name__ == "__main__":
    test_workflow()
