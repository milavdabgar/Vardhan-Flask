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
    status = db.Column(db.String(20))  # open, assigned, in_progress, resolved, closed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    institution = db.Column(db.String(200), nullable=False)
    location_details = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)

    # Relationships
    updates = db.relationship('TicketUpdate', backref='service_request', lazy='dynamic')

class TicketUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    update_type = db.Column(db.String(20))  # status_change, comment, resolution
    comment = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to get user details
    updated_by_user = db.relationship('User', foreign_keys=[updated_by])
