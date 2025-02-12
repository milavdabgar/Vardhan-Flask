from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.service_requests import bp
from app import db
from app.models import (
    ServiceRequest, User, TicketUpdate, RequestFeedback,
    TechnicianAssignment, AMCContract, Equipment
)
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
                         requests=requests,
                         now=datetime.now())

@bp.route('/request/new', methods=['GET', 'POST'])
@login_required
def create_request():
    if current_user.role != 'college_admin':
        flash('Only college administrators can create service requests.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Create new service request with basic info
        service_request = ServiceRequest(
            title=request.form['title'],
            description=request.form['description'],
            priority=request.form['priority'],
            institution=current_user.institution,
            created_by=current_user.id,
            status='NEW',
            created_at=datetime.utcnow(),
            ticket_number=generate_ticket_number(),
            problem_category=request.form['problem_category']
        )
        
        # Handle location details
        service_request.building = request.form.get('building')
        service_request.floor = request.form.get('floor')
        service_request.room = request.form.get('room')
        service_request.area_details = request.form.get('area_details')
        
        # Handle category-specific fields
        if service_request.problem_category == 'single_equipment':
            service_request.contract_id = request.form.get('contract_id')
            service_request.equipment_id = request.form.get('equipment_id')
            service_request.equipment_type = Equipment.query.get(request.form.get('equipment_id')).type
        
        elif service_request.problem_category in ['network', 'wifi']:
            service_request.issue_type = request.form.get('issue_type')
            service_request.affected_users = request.form.get('affected_users')
            
            # For network/wifi issues, get the contract automatically
            active_contract = AMCContract.query.filter_by(
                institution=current_user.institution,
                status='ACTIVE',
                contract_type='network'
            ).first()
            if active_contract:
                service_request.contract_id = active_contract.id
        
        # Auto-assign to Jr. Technician based on contract
        if service_request.contract_id:
            jr_tech = User.query.join(TechnicianAssignment).filter(
                TechnicianAssignment.contract_id == service_request.contract_id,
                TechnicianAssignment.is_senior == False
            ).first()
            
            if jr_tech:
                service_request.assigned_to = jr_tech.id
            else:
                flash('No junior technician assigned to this contract. Request will be pending assignment.', 'warning')
        else:
            flash('No active contract found for this type of service. Request will be pending assignment.', 'warning')
        
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
    
    # Get active contracts for the institution
    active_contracts = AMCContract.query.filter_by(
        institution=current_user.institution,
        status='ACTIVE'
    ).all()
    
    return render_template('service_requests/create_request.html', 
                          title='New Service Request',
                          contracts=active_contracts)

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
    
    # Get contracts for the institution
    from app.models import AMCContract
    contracts = AMCContract.query.filter_by(
        institution=current_user.institution,
        status='ACTIVE'
    ).all()
    
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
        if action == 'edit' and current_user.role == 'college_admin':
            if service_request.status != 'NEW' or service_request.created_by != current_user.id:
                flash('Can only edit requests in NEW state that you created.', 'danger')
                return redirect(url_for('service_requests.view_request', request_id=request_id))
                
            # Update basic info
            service_request.title = request.form.get('title', service_request.title)
            service_request.description = request.form.get('description', service_request.description)
            service_request.priority = request.form.get('priority', service_request.priority)
            service_request.problem_category = request.form.get('problem_category', service_request.problem_category)
            
            # Update location details
            service_request.building = request.form.get('building')
            service_request.floor = request.form.get('floor')
            service_request.room = request.form.get('room')
            service_request.area_details = request.form.get('area_details')
            
            # Handle category-specific fields
            if service_request.problem_category == 'single_equipment':
                service_request.contract_id = request.form.get('contract_id')
                service_request.equipment_id = request.form.get('equipment_id')
                if service_request.equipment_id:
                    service_request.equipment_type = Equipment.query.get(service_request.equipment_id).type
            
            elif service_request.problem_category in ['network', 'wifi', 'cctv', 'infrastructure']:
                service_request.issue_type = request.form.get('issue_type')
                service_request.affected_users = request.form.get('affected_users')
                
                # For network/wifi issues, get the contract automatically
                if service_request.problem_category in ['network', 'wifi']:
                    active_contract = AMCContract.query.filter_by(
                        institution=current_user.institution,
                        status='ACTIVE',
                        contract_type='network'
                    ).first()
                    if active_contract:
                        service_request.contract_id = active_contract.id
            
            # Auto-assign to Jr. Technician based on contract if not already assigned
            if service_request.contract_id and not service_request.assigned_to:
                jr_tech = User.query.join(TechnicianAssignment).filter(
                    TechnicianAssignment.contract_id == service_request.contract_id,
                    TechnicianAssignment.is_senior == False
                ).first()
                
                if jr_tech:
                    service_request.assigned_to = jr_tech.id
                    comment = 'Request details updated and assigned to junior technician'
                else:
                    comment = 'Request details updated (no junior technician available for assignment)'
            
        elif action in ['schedule', 'reschedule'] and current_user.role == 'technician':
            # Validate required fields
            scheduled_date = request.form.get('scheduled_date')
            scheduled_time = request.form.get('scheduled_time')
            
            # For reschedule, verify assigned technician
            if action == 'reschedule' and service_request.assigned_to != current_user.id:
                flash('Only the assigned technician can reschedule visits.', 'danger')
                return redirect(url_for('service_requests.view_request', request_id=request_id))
            
            if not scheduled_date or not scheduled_time:
                flash('Please provide both date and time for the visit.', 'danger')
                return redirect(url_for('service_requests.update_request', request_id=request_id))
            
            try:
                # Parse and validate date/time
                scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
                scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
                
                # Check if date is not in past
                if scheduled_date < datetime.now().date():
                    flash('Cannot schedule visit for a past date.', 'danger')
                    return redirect(url_for('service_requests.update_request', request_id=request_id))
                
                # Set new status based on current status
                if service_request.status == 'REOPENED':
                    new_status = 'VISITED'
                elif service_request.status == 'ON_HOLD':
                    new_status = 'SCHEDULED'  # Move from ON_HOLD back to SCHEDULED
                else:
                    new_status = 'SCHEDULED'
                
                service_request.scheduled_date = scheduled_date
                service_request.scheduled_time = scheduled_time
                service_request.scheduled_at = datetime.utcnow()
                
                comment = f"Visit scheduled for {service_request.format_schedule_time()}"
                if request.form.get('comment'):
                    comment += f"\nNotes: {request.form.get('comment')}"
                    
            except ValueError:
                flash('Invalid date or time format provided.', 'danger')
                return redirect(url_for('service_requests.update_request', request_id=request_id))
            
        elif action == 'mark_visited' and current_user.role == 'college_admin':
            new_status = 'VISITED'
            service_request.visited_at = datetime.utcnow()
            service_request.actual_visit_time = datetime.utcnow()
            service_request.visit_count += 1
            
            # Auto-escalate to Sr. Technician if multiple visits
            if service_request.visit_count > 1:
                # Get active contract for this institution
                from app.models import AMCContract
                active_contract = AMCContract.query.filter_by(
                    institution=service_request.institution,
                    status='ACTIVE'
                ).first()
                
                sr_tech = None
                if active_contract:
                    sr_tech = User.query.join(TechnicianAssignment).filter(
                        TechnicianAssignment.contract_id == active_contract.id,
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
            
        elif action == 'resolve' and current_user.role in ['technician', 'college_admin']:
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
            sr_tech = User.query.join(TechnicianAssignment)\
                .join(AMCContract)\
                .filter(
                    AMCContract.institution == service_request.institution,
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
            
            # Get rating and feedback
            try:
                rating = int(request.form.get('rating', 5))  # Default to 5 stars if not provided
                if not 1 <= rating <= 5:
                    rating = 5  # Ensure rating is between 1-5
            except (ValueError, TypeError):
                rating = 5  # Default to 5 stars if invalid value
                
            feedback_text = request.form.get('feedback', '').strip()
            if not feedback_text:
                feedback_text = 'No feedback provided'
            
            # Create feedback
            feedback = RequestFeedback(
                service_request_id=service_request.id,
                rating=rating,
                comments=feedback_text,
                created_by=current_user.id,
                is_auto_rated=False
            )
            db.session.add(feedback)
            comment = f'Request closed with {rating}-star rating'
            
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
                         request=service_request,
                         contracts=contracts,
                         status_colors={
                             'NEW': 'info',
                             'ASSIGNED': 'primary',
                             'SCHEDULED': 'warning',
                             'VISITED': 'secondary',
                             'RESOLVED': 'success',
                             'CLOSED': 'dark',
                             'ON_HOLD': 'danger'
                         },
                         priority_colors={
                             'low': 'success',
                             'medium': 'warning',
                             'high': 'danger',
                             'urgent': 'danger'
                         },
                         now=datetime.now())

# API endpoint to get equipment for a contract
@bp.route('/api/contract/<int:contract_id>/equipment')
@login_required
def get_contract_equipment(contract_id):
    # Verify user has access to this contract
    contract = AMCContract.query.filter_by(
        id=contract_id,
        institution=current_user.institution
    ).first_or_404()
    
    equipment = Equipment.query.filter_by(
        contract_id=contract_id,
        status='ACTIVE'
    ).all()
    
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'type': e.type,
        'location': e.location
    } for e in equipment])

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
