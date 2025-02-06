from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.main import bp
from app.models import ServiceRequest, User

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'technician':
            return redirect(url_for('main.technician_dashboard'))
        else:  # college_admin
            return redirect(url_for('main.college_dashboard'))
    return render_template('main/index.html', title='Welcome')

@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Admin sees all tickets and system statistics
    open_tickets = ServiceRequest.query.filter(
        ServiceRequest.status.in_(['open', 'assigned', 'in_progress'])
    ).order_by(ServiceRequest.created_at.desc()).limit(10).all()
    
    total_tickets = ServiceRequest.query.count()
    pending_approvals = User.query.filter_by(is_active=False).count()
    active_technicians = User.query.filter_by(role='technician', is_active=True).count()
    
    return render_template('main/admin_dashboard.html', 
                         title='Admin Dashboard',
                         open_tickets=open_tickets,
                         total_tickets=total_tickets,
                         pending_approvals=pending_approvals,
                         active_technicians=active_technicians)

@bp.route('/technician/dashboard')
@login_required
def technician_dashboard():
    if current_user.role != 'technician':
        flash('Access denied. Technician privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Technician sees assigned tickets
    assigned_tickets = ServiceRequest.query.filter(
        ServiceRequest.assigned_to == current_user.id,
        ServiceRequest.status.in_(['assigned', 'in_progress'])
    ).order_by(ServiceRequest.created_at.desc()).all()
    
    completed_tickets = ServiceRequest.query.filter(
        ServiceRequest.assigned_to == current_user.id,
        ServiceRequest.status == 'resolved'
    ).count()
    
    return render_template('main/technician_dashboard.html',
                         title='Technician Dashboard',
                         assigned_tickets=assigned_tickets,
                         completed_tickets=completed_tickets)

@bp.route('/college/dashboard')
@login_required
def college_dashboard():
    if current_user.role != 'college_admin':
        flash('Access denied. College Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # College admin sees their institution's tickets
    college_tickets = ServiceRequest.query.filter(
        ServiceRequest.institution == current_user.institution
    ).order_by(ServiceRequest.created_at.desc()).all()
    
    open_tickets = [t for t in college_tickets if t.status in ['open', 'assigned', 'in_progress']]
    resolved_tickets = [t for t in college_tickets if t.status == 'resolved']
    
    return render_template('main/college_dashboard.html',
                         title='College Dashboard',
                         open_tickets=open_tickets,
                         resolved_tickets=resolved_tickets)
