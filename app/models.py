from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # admin, technician, college_admin
    full_name = db.Column(db.String(100))
    contact_number = db.Column(db.String(15))
    institution = db.Column(db.String(200))  # For college admins
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    created_requests = db.relationship('ServiceRequest', 
                                    foreign_keys='ServiceRequest.created_by',
                                    backref=db.backref('created_by_user', lazy=True))
    assigned_requests = db.relationship('ServiceRequest', 
                                     foreign_keys='ServiceRequest.assigned_to',
                                     backref=db.backref('assigned_to_user', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    equipment_type = db.Column(db.String(50))  # computer, printer, cctv, etc.
    priority = db.Column(db.String(20))  # low, medium, high, urgent
    status = db.Column(db.String(20), default='requested', nullable=False)  # States: requested, assigned, accepted, working, completed, closed, rejected, on_hold, reopened
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_sr_created_by'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_sr_assigned_to'))
    institution = db.Column(db.String(200), nullable=False)
    location_details = db.Column(db.String(200))

    # Scheduling fields
    scheduled_date = db.Column(db.Date)
    scheduled_time = db.Column(db.Time)
    actual_start_time = db.Column(db.DateTime)

    # Timestamps for each status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime)
    accepted_at = db.Column(db.DateTime)
    working_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    on_hold_at = db.Column(db.DateTime)
    reopened_at = db.Column(db.DateTime)

    # Additional fields for status tracking
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_sr_assigned_by'))
    estimated_completion_time = db.Column(db.DateTime)
    hold_reason = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    resolution_notes = db.Column(db.Text)
    progress_notes = db.Column(db.Text)

    # Relationships
    updates = db.relationship('TicketUpdate', backref='service_request', lazy='dynamic')
    feedback = db.relationship('RequestFeedback', backref='service_request', uselist=False)
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_by_requests')

    def can_transition_to(self, new_status):
        """Check if the status transition is valid"""
        valid_transitions = {
            'requested': ['assigned', 'rejected'],  # New request can be assigned or rejected
            'assigned': ['accepted', 'rejected'],   # Assigned technician can accept or reject
            'accepted': ['scheduled'],             # After accepting, technician must schedule visit
            'scheduled': ['pending_approval'],     # When technician arrives, they request start approval
            'pending_approval': ['working', 'scheduled'],  # Admin can approve start or request reschedule
            'working': ['completed', 'on_hold'],   # Work can be completed or put on hold
            'completed': ['closed', 'reopened'],   # College admin can close or request changes
            'closed': ['reopened'],               # Closed requests can be reopened if issues found
            'rejected': ['requested'],            # Rejected goes back to requested for reassignment
            'on_hold': ['working'],              # On-hold work can be resumed
            'reopened': ['scheduled']            # Reopened requests need new visit scheduled
        }
        return new_status in valid_transitions.get(self.status, [])

    def get_status_badge_color(self):
        """Get the appropriate badge color for the status"""
        colors = {
            'requested': 'warning',     # yellow - needs attention
            'assigned': 'info',         # blue - in system
            'accepted': 'primary',      # blue - acknowledged
            'scheduled': 'info',        # blue - planned
            'pending_approval': 'warning', # yellow - needs attention
            'working': 'primary',       # blue - active work
            'completed': 'success',     # green - work done
            'closed': 'secondary',      # gray - finished
            'rejected': 'danger',       # red - needs attention
            'on_hold': 'warning',       # yellow - needs attention
            'reopened': 'warning'       # yellow - needs attention
        }
        return colors.get(self.status, 'secondary')

    def get_status_display(self):
        """Get a user-friendly status display message"""
        messages = {
            'requested': 'New Request',
            'assigned': 'Assigned to Technician',
            'accepted': 'Accepted by Technician',
            'scheduled': 'Visit Scheduled',
            'pending_approval': 'Awaiting Start Authorization',
            'working': 'Work in Progress',
            'completed': 'Work Completed',
            'closed': 'Request Closed',
            'rejected': 'Request Rejected',
            'on_hold': 'Work On Hold',
            'reopened': 'Request Reopened'
        }
        return messages.get(self.status, self.status.title())

    def get_allowed_actions(self, user_role):
        """Get allowed actions based on current status and user role"""
        actions = []
        
        if user_role == 'admin':
            if self.status == 'requested':
                actions.extend([('assign', 'Assign Technician', 'primary')])
            elif self.status == 'rejected':
                actions.extend([('assign', 'Reassign Technician', 'primary')])
        
        elif user_role == 'technician':
            if self.status == 'assigned':
                actions.extend([
                    ('accept', 'Accept Assignment', 'success'),
                    ('reject', 'Reject Assignment', 'danger')
                ])
            elif self.status == 'accepted':
                actions.extend([('schedule', 'Schedule Visit', 'primary')])
            elif self.status == 'scheduled':
                actions.extend([('request_approval', 'Request Start Authorization', 'primary')])
            elif self.status == 'working':
                actions.extend([
                    ('complete', 'Mark as Complete', 'success'),
                    ('hold', 'Put on Hold', 'warning')
                ])
            elif self.status == 'on_hold':
                actions.extend([('resume', 'Resume Work', 'primary')])
            elif self.status == 'reopened':
                actions.extend([('schedule', 'Schedule New Visit', 'primary')])
        
        elif user_role == 'college_admin':
            if self.status == 'pending_approval':
                actions.extend([
                    ('approve_start', 'Authorize Work Start', 'success'),
                    ('reschedule', 'Request Different Time', 'warning')
                ])
            elif self.status == 'completed':
                actions.extend([
                    ('approve', 'Approve & Close', 'success'),
                    ('reopen', 'Request Changes', 'danger')
                ])
            elif self.status == 'closed':
                actions.extend([('reopen', 'Reopen Request', 'warning')])
        
        return actions

    def format_schedule_time(self):
        """Format scheduled date and time for display"""
        if self.scheduled_date and self.scheduled_time:
            return f"{self.scheduled_date.strftime('%Y-%m-%d')} at {self.scheduled_time.strftime('%I:%M %p')}"
        return "Not scheduled"

class RequestFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id', name='fk_rf_service_request'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars
    comments = db.Column(db.Text)
    resolution_satisfaction = db.Column(db.Boolean)  # True if satisfied
    time_satisfaction = db.Column(db.Boolean)  # True if satisfied with resolution time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_rf_created_by'), nullable=False)

    # Relationship to get user details
    created_by_user = db.relationship('User', foreign_keys=[created_by])

class TicketUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id', name='fk_tu_service_request'), nullable=False)
    update_type = db.Column(db.String(20))  # status_change, comment, progress_update
    previous_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    comment = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_tu_updated_by'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to get user details
    updated_by_user = db.relationship('User', foreign_keys=[updated_by])
