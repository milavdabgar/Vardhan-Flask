from flask_apscheduler import APScheduler
from app import create_app, db
from app.models import ServiceRequest, RequestFeedback, TicketUpdate
from datetime import datetime, timedelta

scheduler = APScheduler()

def auto_close_resolved_task():
    """Background task to auto-close resolved requests and assign 5-star ratings"""
    print(f"[{datetime.utcnow()}] Running auto-close task...")
    with scheduler.app.app_context():
        # Find requests that have been resolved for more than 60 seconds
        cutoff_time = datetime.utcnow() - timedelta(seconds=60)
        print(f"Looking for requests resolved before {cutoff_time}")
        
        resolved_requests = ServiceRequest.query.filter(
            ServiceRequest.status == 'RESOLVED',
            ServiceRequest.resolved_at <= cutoff_time
        ).all()
        
        print(f"Found {len(resolved_requests)} resolved requests")
        for sr in resolved_requests:
            print(f"Request {sr.ticket_number}: resolved_at={sr.resolved_at}, reopen_deadline={sr.reopen_deadline}")
        
        for sr in resolved_requests:
            sr.status = 'CLOSED'
            sr.closed_at = datetime.utcnow()
            sr.auto_closed = True
            
            # Create 5-star feedback
            feedback = RequestFeedback(
                service_request_id=sr.id,
                rating=5,
                comments='Automatically closed after 7 days with no issues reported',
                created_by=sr.created_by,
                is_auto_rated=True
            )
            db.session.add(feedback)
            
            update = TicketUpdate(
                service_request_id=sr.id,
                update_type='status_change',
                previous_status='RESOLVED',
                new_status='CLOSED',
                comment='Automatically closed after 7 days with 5-star rating',
                updated_by=sr.created_by
            )
            db.session.add(update)
        
        db.session.commit()

def init_scheduler(app):
    """Initialize the scheduler with the Flask app"""
    print("Initializing scheduler...")
    scheduler.init_app(app)
    scheduler.api_enabled = True  # Enable the API for debugging
    
    # Add job to run every 30 seconds for testing
    scheduler.add_job(
        id='auto_close_resolved',
        func=auto_close_resolved_task,
        trigger='interval',
        seconds=30
    )
    
    scheduler.start()
