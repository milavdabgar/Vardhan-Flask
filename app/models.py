from datetime import datetime, timedelta
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

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class TechnicianAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_ta_technician'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('amc_contract.id', name='fk_ta_contract'), nullable=False)
    is_senior = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    technician = db.relationship('User', backref='contract_assignments')
    contract = db.relationship('AMCContract', backref='technician_assignments')

    def __repr__(self):
        return f'<TechnicianAssignment {self.technician.full_name} - {self.contract.contract_number}>'

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    equipment_type = db.Column(db.String(50))  # computer, printer, cctv, etc.
    priority = db.Column(db.String(20))  # low, medium, high, urgent
    status = db.Column(db.String(20), default='NEW', nullable=False)  # NEW, SCHEDULED, VISITED, ON_HOLD, RESOLVED, REOPENED, CLOSED
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_sr_created_by'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_sr_assigned_to'))
    institution = db.Column(db.String(200), nullable=False)
    location_details = db.Column(db.String(200))

    # Scheduling fields
    scheduled_date = db.Column(db.Date)
    scheduled_time = db.Column(db.Time)
    actual_visit_time = db.Column(db.DateTime)
    visit_count = db.Column(db.Integer, default=0)  # Track number of visits

    # Timestamps for each status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_at = db.Column(db.DateTime)
    visited_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    reopened_at = db.Column(db.DateTime)
    on_hold_at = db.Column(db.DateTime)

    # Additional fields
    on_hold_reason = db.Column(db.Text)
    expected_resolution_date = db.Column(db.Date)  # For ON_HOLD status
    resolution_notes = db.Column(db.Text)
    auto_closed = db.Column(db.Boolean, default=False)  # Track if closed automatically after 7 days
    reopen_deadline = db.Column(db.DateTime)  # 7-day window for reopening

    # Relationships
    updates = db.relationship('TicketUpdate', backref='service_request', lazy='dynamic')
    feedback = db.relationship('RequestFeedback', backref='service_request', uselist=False)

    def can_transition_to(self, new_status):
        """Check if the status transition is valid"""
        valid_transitions = {
            'NEW': ['SCHEDULED'],
            'SCHEDULED': ['VISITED', 'ON_HOLD'],
            'VISITED': ['RESOLVED', 'ON_HOLD'],
            'ON_HOLD': ['SCHEDULED', 'VISITED'],
            'RESOLVED': ['REOPENED', 'CLOSED'],
            'REOPENED': ['VISITED'],
            'CLOSED': []  # No transitions from CLOSED state
        }
        return new_status in valid_transitions.get(self.status, [])

    def get_status_badge_color(self):
        """Get the appropriate badge color for the status"""
        colors = {
            'NEW': 'info',
            'SCHEDULED': 'primary',
            'VISITED': 'warning',
            'ON_HOLD': 'warning',
            'RESOLVED': 'success',
            'REOPENED': 'danger',
            'CLOSED': 'secondary'
        }
        return colors.get(self.status, 'secondary')

    def get_status_display(self):
        """Get a user-friendly status display message"""
        return self.status.title().replace('_', ' ')

    def get_allowed_actions(self, user):
        """Get allowed actions based on current status and user role"""
        actions = []
        
        # First check if user is college admin and request is in NEW state
        if user.role == 'college_admin' and self.status == 'NEW' and self.created_by == user.id:
            actions.extend([('edit', 'Edit Request', 'info')])

        # Then check technician actions
        if user.role == 'technician':
            # Get active contract for this institution
            active_contract = AMCContract.query.filter_by(
                institution=self.institution,
                status='ACTIVE'
            ).first()
            
            # Check if user is a senior technician for this contract
            is_senior = False
            if active_contract:
                is_senior = any(assignment.is_senior for assignment in user.contract_assignments 
                               if assignment.contract_id == active_contract.id)
            
            if self.status == 'NEW' and not is_senior:
                actions.extend([('schedule', 'Schedule Visit', 'primary')])
            elif self.status == 'SCHEDULED' and self.assigned_to == user.id:
                actions.extend([('reschedule', 'Reschedule Visit', 'warning')])
            elif self.status == 'VISITED':
                actions.extend([
                    ('resolve', 'Mark as Resolved', 'success'),
                    ('hold', 'Put on Hold', 'warning')
                ])
            elif self.status == 'ON_HOLD':
                actions.extend([('resume', 'Resume Work', 'primary')])
            elif self.status == 'REOPENED' and is_senior:
                actions.extend([('schedule', 'Schedule New Visit', 'primary')])
        
        # Then check remaining college admin actions
        elif user.role == 'college_admin':
            if self.status == 'SCHEDULED':
                actions.extend([('mark_visited', 'Mark as Visited', 'success')])
            elif self.status == 'VISITED':
                actions.extend([('resolve', 'Mark as Resolved', 'success')])
            elif self.status == 'RESOLVED':
                if datetime.utcnow() < self.reopen_deadline:
                    actions.extend([('reopen', 'Reopen Request', 'warning')])
                actions.extend([('close', 'Close with Feedback', 'success')])
            elif self.status == 'CLOSED':
                actions.extend([('update_feedback', 'Update Feedback', 'primary')])
        
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_rf_created_by'), nullable=False)
    is_auto_rated = db.Column(db.Boolean, default=False)  # True if system assigned 5-star rating

    # Relationship to get user details
    created_by_user = db.relationship('User', foreign_keys=[created_by])

class TicketUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id', name='fk_tu_service_request'), nullable=False)
    update_type = db.Column(db.String(20))  # status_change, comment
    previous_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    comment = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_tu_updated_by'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to get user details
    updated_by_user = db.relationship('User', foreign_keys=[updated_by])

class AMCContract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    institution = db.Column(db.String(100), nullable=False)
    contract_type = db.Column(db.String(50), nullable=False)  # CWAN & CCTV or Computer and Printers
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    contract_value = db.Column(db.Float, nullable=False)
    payment_terms = db.Column(db.Text)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, EXPIRED, TERMINATED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='contracts_created', foreign_keys=[created_by])
    equipments = db.relationship('Equipment', backref='contract', lazy=True)

    def days_until_expiry(self):
        if not self.end_date:
            return 0
        today = datetime.now().date()
        if self.end_date < today:
            return 0
        return (self.end_date - today).days

    def is_active(self):
        return self.status == 'ACTIVE' and self.days_until_expiry() > 0

    def __repr__(self):
        return f'<AMCContract {self.contract_number}>'

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Computer, Printer, CCTV, Network Device etc.
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    serial_number = db.Column(db.String(50), unique=True)
    installation_date = db.Column(db.Date)
    location = db.Column(db.String(200))  # Specific location within the institution
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE, UNDER_REPAIR
    specifications = db.Column(db.Text)  # JSON field for additional specs
    contract_id = db.Column(db.Integer, db.ForeignKey('amc_contract.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Equipment {self.name} - {self.serial_number}>'

    def is_under_warranty(self):
        if self.installation_date:
            warranty_end = self.installation_date + timedelta(days=365)  # 1 year warranty
            return datetime.now().date() <= warranty_end
        return False
