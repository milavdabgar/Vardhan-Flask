from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.service_requests import bp
from app.models import ServiceRequest, User, TicketUpdate, RequestFeedback
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
        requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    elif current_user.role == 'technician':
        requests = ServiceRequest.query.filter_by(assigned_to=current_user.id).order_by(ServiceRequest.created_at.desc()).all()
    else:
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
            status='requested',
            created_at=datetime.utcnow(),
            ticket_number=generate_ticket_number()
        )
        db.session.add(service_request)
        db.session.commit()
        
        update = TicketUpdate(
            service_request_id=service_request.id,
            update_type='status_change',
            comment='Service request created',
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
    
    if current_user.role == 'college_admin' and service_request.institution != current_user.institution:
        flash('Access denied. You can only view requests from your institution.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    elif current_user.role == 'technician' and service_request.assigned_to != current_user.id:
        flash('Access denied. You can only view requests assigned to you.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    
    return render_template('service_requests/view_request.html',
                         title=f'Request #{service_request.ticket_number}',
                         request=service_request)

@bp.route('/request/<int:request_id>/update', methods=['GET', 'POST'])
@login_required
def update_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if current_user.role == 'college_admin' and service_request.institution != current_user.institution:
        flash('Access denied. You can only update requests from your institution.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    elif current_user.role == 'technician' and service_request.assigned_to != current_user.id:
        flash('Access denied. You can only update requests assigned to you.', 'danger')
        return redirect(url_for('service_requests.list_requests'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        comment = request.form.get('comment', '').strip()
        new_status = None
        
        # Handle different actions
        if action == 'assign' and current_user.role == 'admin':
            new_status = 'assigned'
            service_request.assigned_to = request.form['assigned_to']
            service_request.assigned_by = current_user.id
            service_request.assigned_at = datetime.utcnow()
        
        elif action == 'accept' and current_user.role == 'technician':
            new_status = 'accepted'
            service_request.accepted_at = datetime.utcnow()
            service_request.estimated_completion_time = datetime.strptime(
                request.form['estimated_completion'], '%Y-%m-%dT%H:%M'
            )
        
        elif action == 'reject' and current_user.role == 'technician':
            new_status = 'rejected'
            service_request.rejection_reason = request.form['rejection_reason']
            comment = f"Rejected - Reason: {service_request.rejection_reason}"
        
        elif action == 'start_work' and current_user.role == 'technician':
            new_status = 'working'
            service_request.working_at = datetime.utcnow()
        
        elif action == 'complete' and current_user.role == 'technician':
            new_status = 'completed'
            service_request.completed_at = datetime.utcnow()
            if request.form.get('progress_notes'):
                service_request.progress_notes = request.form['progress_notes']
        
        elif action == 'hold' and current_user.role == 'technician':
            new_status = 'on_hold'
            service_request.on_hold_at = datetime.utcnow()
            service_request.hold_reason = request.form['hold_reason']
            comment = f"Put on hold - Reason: {service_request.hold_reason}"
        
        elif action == 'resume' and current_user.role == 'technician':
            new_status = 'working'
            service_request.working_at = datetime.utcnow()
        
        elif action == 'approve' and current_user.role == 'college_admin':
            new_status = 'closed'
            service_request.closed_at = datetime.utcnow()
            
            # Create feedback
            feedback = RequestFeedback(
                service_request_id=service_request.id,
                rating=int(request.form['rating']),
                comments=request.form['feedback_comments'],
                resolution_satisfaction=bool(request.form.get('resolution_satisfaction')),
                time_satisfaction=bool(request.form.get('time_satisfaction')),
                created_by=current_user.id
            )
            db.session.add(feedback)
            comment = 'Request approved and closed with feedback'
        
        elif action == 'reopen' and current_user.role == 'college_admin':
            new_status = 'reopened'
            service_request.reopened_at = datetime.utcnow()
            comment = 'Request reopened for changes: ' + comment if comment else 'Request reopened for changes'
        
        elif action == 'schedule' and current_user.role == 'technician':
            new_status = 'scheduled'
            # Convert form date and time to Python objects
            scheduled_date = datetime.strptime(request.form['scheduled_date'], '%Y-%m-%d').date()
            scheduled_time = datetime.strptime(request.form['scheduled_time'], '%H:%M').time()
            service_request.scheduled_date = scheduled_date
            service_request.scheduled_time = scheduled_time
            comment = f"Visit scheduled for {service_request.format_schedule_time()}"
            flash('Visit has been scheduled. College admin will be notified.', 'success')
            
        elif action == 'request_approval' and current_user.role == 'technician':
            new_status = 'pending_approval'
            service_request.actual_start_time = datetime.utcnow()
            comment = "Technician has arrived and requests authorization to start work"
            flash('Waiting for college admin to authorize work start.', 'info')
            
        elif action == 'approve_start' and current_user.role == 'college_admin':
            new_status = 'working'
            service_request.working_at = datetime.utcnow()
            comment = "Work start authorized by college admin"
            flash('Work start has been authorized.', 'success')
            
        elif action == 'reschedule' and current_user.role == 'college_admin':
            new_status = 'scheduled'
            reason = request.form.get('reschedule_reason', 'No reason provided')
            comment = f"Different time requested - Reason: {reason}"
            flash('Technician has been asked to schedule a different time.', 'warning')
        
        # Update status if changed
        if new_status and service_request.can_transition_to(new_status):
            service_request.status = new_status
        
        # Create update log
        if comment:
            update = TicketUpdate(
                service_request_id=service_request.id,
                update_type='status_change',
                previous_status=service_request.status,
                new_status=new_status,
                comment=comment,
                updated_by=current_user.id
            )
            db.session.add(update)
        
        try:
            db.session.commit()
            flash('Service request updated successfully.', 'success')
            return redirect(url_for('service_requests.view_request', request_id=request_id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating service request.', 'error')
            current_app.logger.error(f'Error updating service request: {str(e)}')
    
    # GET request - show form
    technicians = None
    if current_user.role == 'admin':
        technicians = User.query.filter_by(role='technician').all()
    
    return render_template('service_requests/update_request.html',
                         title='Update Service Request',
                         request=service_request,
                         technicians=technicians,
                         actions=service_request.get_allowed_actions(current_user.role),
                         now=datetime.now())
