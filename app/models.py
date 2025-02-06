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
    status = db.Column(db.String(20))  # requested, assigned, accepted, attended, resolved, closed, rejected, on_hold, reopened
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_sr_created_by'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_sr_assigned_to'))
    institution = db.Column(db.String(200), nullable=False)
    location_details = db.Column(db.String(200))

    # Timestamps for each status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime)
    accepted_at = db.Column(db.DateTime)
    attended_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
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

    @property
    def current_status_duration(self):
        """Calculate the duration of the current status"""
        status_times = {
            'requested': self.created_at,
            'assigned': self.assigned_at,
            'accepted': self.accepted_at,
            'attended': self.attended_at,
            'resolved': self.resolved_at,
            'closed': self.closed_at,
            'on_hold': self.on_hold_at,
            'reopened': self.reopened_at
        }
        current_status_time = status_times.get(self.status)
        if current_status_time:
            return datetime.utcnow() - current_status_time
        return None

    def can_transition_to(self, new_status):
        """Check if the status transition is valid"""
        valid_transitions = {
            'requested': ['assigned', 'rejected'],
            'assigned': ['accepted', 'rejected'],
            'accepted': ['attended', 'on_hold', 'rejected'],
            'attended': ['resolved', 'on_hold'],
            'resolved': ['closed', 'reopened'],
            'closed': ['reopened'],
            'rejected': ['assigned'],
            'on_hold': ['attended'],
            'reopened': ['attended']
        }
        return new_status in valid_transitions.get(self.status, [])

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
