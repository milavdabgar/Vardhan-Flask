from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.service_requests import bp
from app.models import ServiceRequest, User, TicketUpdate
from app import db
from datetime import datetime

def generate_ticket_number():
    """Generate a unique ticket number"""
    last_ticket = ServiceRequest.query.order_by(ServiceRequest.id.desc()).first()
    if last_ticket:
        last_number = int(last_ticket.ticket_number[3:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f'SR-{new_number:06d}'

@bp.route('/requests')
@login_required
def list_requests():
    if current_user.role == 'admin':
        # Admin sees all requests
        requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    elif current_user.role == 'technician':
        # Technician sees assigned requests
        requests = ServiceRequest.query.filter_by(assigned_to=current_user.id).order_by(ServiceRequest.created_at.desc()).all()
    else:
        # College admin sees their institution's requests
        requests = ServiceRequest.query.filter_by(institution=current_user.institution).order_by(ServiceRequest.created_at.desc()).all()
    
    return render_template('service_requests/list_requests.html', 
                         title='Service Requests',
                         requests=requests)

@bp.route('/request/new', methods=['GET', 'POST'])
@login_required
def create_request():
    if current_user.role != 'college_admin':
        flash('Only college administrators can create service requests.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        service_request = ServiceRequest(
            title=request.form['title'],
            description=request.form['description'],
            equipment_type=request.form['equipment_type'],
            priority=request.form['priority'],
            institution=current_user.institution,
            created_by=current_user.id,
            status='open',
            created_at=datetime.utcnow(),
            ticket_number=generate_ticket_number()
        )
        db.session.add(service_request)
        db.session.commit()
        
        # Create initial ticket update
        update = TicketUpdate(
            service_request_id=service_request.id,
            update_type='status_change',
            comment='Ticket created',
            updated_by=current_user.id
        )
        db.session.add(update)
        db.session.commit()
        
        flash('Service request created successfully.', 'success')
        return redirect(url_for('service_requests.list_requests'))
    
    return render_template('service_requests/create_request.html', title='New Service Request')

@bp.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    # Check access permissions
    if current_user.role == 'college_admin' and service_request.institution != current_user.institution:
        flash('Access denied. You can only view requests from your institution.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    elif current_user.role == 'technician' and service_request.assigned_to != current_user.id:
        flash('Access denied. You can only view requests assigned to you.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    
    return render_template('service_requests/view_request.html',
                         title=f'Request #{service_request.id}',
                         request=service_request)

@bp.route('/request/<int:request_id>/update', methods=['GET', 'POST'])
@login_required
def update_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    # Check access permissions
    if current_user.role not in ['admin', 'technician']:
        flash('Access denied. Only administrators and technicians can update requests.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    
    if current_user.role == 'technician' and service_request.assigned_to != current_user.id:
        flash('Access denied. You can only update requests assigned to you.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    
    if request.method == 'POST':
        old_status = service_request.status
        service_request.status = request.form['status']
        if current_user.role == 'admin':
            if 'assigned_to' in request.form:
                service_request.assigned_to = request.form['assigned_to']
        
        if service_request.status == 'resolved':
            service_request.resolved_at = datetime.utcnow()
        
        update = TicketUpdate(
            service_request_id=service_request.id,
            update_type='status_change' if old_status != service_request.status else 'comment',
            comment=request.form.get('comment', ''),
            updated_by=current_user.id
        )
        db.session.add(update)
        db.session.commit()
        flash('Service request updated successfully.', 'success')
        return redirect(url_for('service_requests.view_request', request_id=request_id))
    
    technicians = None
    if current_user.role == 'admin':
        technicians = User.query.filter_by(role='technician', is_active=True).all()
    
    return render_template('service_requests/update_request.html',
                         title=f'Update Request #{service_request.id}',
                         request=service_request,
                         technicians=technicians)
