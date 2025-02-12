from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.service_requests import bp
from app.models import ServiceRequest, User, TicketUpdate, RequestFeedback, TechnicianAssignment
from app import db
from datetime import datetime, timedelta

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
        # Create new service request
        service_request = ServiceRequest(
            title=request.form['title'],
            description=request.form['description'],
            equipment_type=request.form['equipment_type'],
            priority=request.form['priority'],
            institution=current_user.institution,
            created_by=current_user.id,
            status='NEW',
            created_at=datetime.utcnow(),
            ticket_number=generate_ticket_number()
        )
        
        # Auto-assign to Jr. Technician
        jr_tech = User.query.join(TechnicianAssignment).filter(
            TechnicianAssignment.college == current_user.institution,
            TechnicianAssignment.is_senior == False
        ).first()
        
        if jr_tech:
            service_request.assigned_to = jr_tech.id
        else:
            flash('No junior technician assigned to your college. Request will be pending assignment.', 'warning')
        
        db.session.add(service_request)
        db.session.commit()
        
        update = TicketUpdate(
            service_request_id=service_request.id,
            update_type='status_change',
            comment='Service request created and auto-assigned to junior technician',
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
    
    # Access control
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
        
        # Handle different actions based on the new workflow
        if action == 'schedule' and current_user.role == 'technician':
            new_status = 'SCHEDULED'
            scheduled_date = datetime.strptime(request.form['scheduled_date'], '%Y-%m-%d').date()
            scheduled_time = datetime.strptime(request.form['scheduled_time'], '%H:%M').time()
            service_request.scheduled_date = scheduled_date
            service_request.scheduled_time = scheduled_time
            service_request.scheduled_at = datetime.utcnow()
            comment = f"Visit scheduled for {service_request.format_schedule_time()}"
            
        elif action == 'confirm_visit' and current_user.role == 'college_admin':
            new_status = 'VISITED'
            service_request.visited_at = datetime.utcnow()
            service_request.actual_visit_time = datetime.utcnow()
            service_request.visit_count += 1
            
            # Auto-escalate to Sr. Technician if multiple visits
            if service_request.visit_count > 1:
                sr_tech = User.query.join(TechnicianAssignment).filter(
                    TechnicianAssignment.college == service_request.institution,
                    TechnicianAssignment.is_senior == True
                ).first()
                
                if sr_tech:
                    service_request.assigned_to = sr_tech.id
                    comment += "\nMultiple visits required - Auto-escalated to Senior Technician"
            
        elif action == 'hold' and current_user.role == 'technician':
            new_status = 'ON_HOLD'
            service_request.on_hold_at = datetime.utcnow()
            service_request.on_hold_reason = request.form['hold_reason']
            service_request.expected_resolution_date = datetime.strptime(request.form['expected_resolution_date'], '%Y-%m-%d').date()
            comment = f"Put on hold - Reason: {service_request.on_hold_reason}"
            
        elif action == 'resolve' and current_user.role == 'technician':
            new_status = 'RESOLVED'
            service_request.resolved_at = datetime.utcnow()
            service_request.resolution_notes = request.form.get('resolution_notes')
            service_request.reopen_deadline = datetime.utcnow() + timedelta(days=7)
            comment = "Issue resolved: " + service_request.resolution_notes if service_request.resolution_notes else "Issue resolved"
            
        elif action == 'reopen' and current_user.role == 'college_admin':
            if service_request.reopen_deadline and datetime.utcnow() > service_request.reopen_deadline:
                flash('Cannot reopen - 7-day reopen window has expired.', 'danger')
                return redirect(url_for('service_requests.view_request', request_id=request_id))
                
            new_status = 'REOPENED'
            service_request.reopened_at = datetime.utcnow()
            
            # Auto-assign to Sr. Technician
            sr_tech = User.query.join(TechnicianAssignment).filter(
                TechnicianAssignment.college == service_request.institution,
                TechnicianAssignment.is_senior == True
            ).first()
            
            if sr_tech:
                service_request.assigned_to = sr_tech.id
                comment = f"Request reopened and assigned to senior technician: {comment if comment else 'No specific reason provided'}"
            else:
                flash('No senior technician assigned to your college. Request will be pending assignment.', 'warning')
            
        elif action == 'close' and current_user.role == 'college_admin':
            new_status = 'CLOSED'
            service_request.closed_at = datetime.utcnow()
            
            # Create feedback
            feedback = RequestFeedback(
                service_request_id=service_request.id,
                rating=int(request.form['rating']),
                comments=request.form.get('feedback_comments'),
                created_by=current_user.id,
                is_auto_rated=False
            )
            db.session.add(feedback)
            comment = 'Request closed with feedback'
            
            flash('Request closed successfully. Note: This action cannot be undone.', 'info')
            
        elif action == 'update_feedback' and current_user.role == 'college_admin':
            if service_request.status != 'CLOSED':
                flash('Feedback can only be updated for closed requests.', 'danger')
                return redirect(url_for('service_requests.view_request', request_id=request_id))
                
            feedback = service_request.feedback
            if feedback:
                feedback.rating = int(request.form['rating'])
                feedback.comments = request.form.get('feedback_comments')
                feedback.updated_at = datetime.utcnow()
                comment = 'Feedback updated'
            else:
                flash('No feedback found to update.', 'danger')
                return redirect(url_for('service_requests.view_request', request_id=request_id))
        
        # Update status if changed and transition is valid
        if new_status and service_request.can_transition_to(new_status):
            old_status = service_request.status
            service_request.status = new_status
            
            # Create update log
            if comment:
                update = TicketUpdate(
                    service_request_id=service_request.id,
                    update_type='status_change',
                    previous_status=old_status,
                    new_status=new_status,
                    comment=comment,
                    updated_by=current_user.id
                )
                db.session.add(update)
        
        db.session.commit()
        return redirect(url_for('service_requests.view_request', request_id=request_id))
    
    return render_template('service_requests/update_request.html',
                         title=f'Update Request #{service_request.ticket_number}',
                         request=service_request)

# Background task to auto-close resolved requests and assign 5-star ratings
@bp.route('/auto_close_resolved', methods=['POST'])
def auto_close_resolved():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    resolved_requests = ServiceRequest.query.filter(
        ServiceRequest.status == 'RESOLVED',
        ServiceRequest.resolved_at <= datetime.utcnow() - timedelta(days=7),
        ServiceRequest.reopen_deadline <= datetime.utcnow()
    ).all()
    
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
    return jsonify({'message': f'Auto-closed {len(resolved_requests)} requests'}), 200
