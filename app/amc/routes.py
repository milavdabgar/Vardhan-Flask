from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import AMCContract, Equipment, User, TechnicianAssignment
from app.decorators import admin_required
from app.amc import bp
from app.amc.forms import TechnicianAssignmentForm
from datetime import datetime

@bp.route('/contracts')
@login_required
def list_contracts():
    contracts = AMCContract.query.all()
    return render_template('amc/contracts.html', contracts=contracts, title='AMC Contracts')

@bp.route('/contracts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_contract():
    if request.method == 'POST':
        contract = AMCContract(
            contract_number=request.form['contract_number'],
            institution=request.form['institution'],
            contract_type=request.form['contract_type'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            contract_value=float(request.form['contract_value']),
            payment_terms=request.form['payment_terms'],
            created_by=current_user.id
        )
        db.session.add(contract)
        try:
            db.session.commit()
            flash('Contract created successfully.', 'success')
            return redirect(url_for('amc.view_contract', id=contract.id))
        except Exception as e:
            db.session.rollback()
            flash('Error creating contract. Please try again.', 'danger')
            return render_template('amc/contract_form.html', title='New Contract')
    
    return render_template('amc/contract_form.html', title='New Contract')

@bp.route('/contracts/<int:id>')
@login_required
def view_contract(id):
    contract = AMCContract.query.get_or_404(id)
    return render_template('amc/contract_detail.html', contract=contract, title='Contract Details')

@bp.route('/contracts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_contract(id):
    contract = AMCContract.query.get_or_404(id)
    if request.method == 'POST':
        contract.contract_number = request.form['contract_number']
        contract.institution = request.form['institution']
        contract.contract_type = request.form['contract_type']
        contract.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        contract.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        contract.contract_value = float(request.form['contract_value'])
        contract.payment_terms = request.form['payment_terms']
        contract.status = request.form.get('status', contract.status)
        
        try:
            db.session.commit()
            flash('Contract updated successfully.', 'success')
            return redirect(url_for('amc.view_contract', id=contract.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating contract. Please try again.', 'danger')
    
    return render_template('amc/contract_form.html', contract=contract, title='Edit Contract')

@bp.route('/equipment')
@login_required
def list_equipment():
    equipment = Equipment.query.all()
    return render_template('amc/equipment.html', equipment=equipment, title='Equipment')

@bp.route('/equipment/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_equipment():
    contracts = AMCContract.query.filter_by(status='ACTIVE').all()
    if request.method == 'POST':
        equipment = Equipment(
            name=request.form['name'],
            type=request.form['type'],
            make=request.form['make'],
            model=request.form['model'],
            serial_number=request.form['serial_number'],
            installation_date=datetime.strptime(request.form['installation_date'], '%Y-%m-%d').date() if request.form['installation_date'] else None,
            location=request.form['location'],
            specifications=request.form['specifications'],
            contract_id=request.form['contract_id']
        )
        db.session.add(equipment)
        try:
            db.session.commit()
            flash('Equipment added successfully.', 'success')
            return redirect(url_for('amc.view_equipment', id=equipment.id))
        except Exception as e:
            db.session.rollback()
            flash('Error adding equipment. Please try again.', 'danger')
    
    return render_template('amc/equipment_form.html', contracts=contracts, title='New Equipment')

@bp.route('/equipment/<int:id>')
@login_required
def view_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    return render_template('amc/equipment_detail.html', equipment=equipment, title='Equipment Details')

@bp.route('/equipment/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    contracts = AMCContract.query.filter_by(status='ACTIVE').all()
    if request.method == 'POST':
        equipment.name = request.form['name']
        equipment.type = request.form['type']
        equipment.make = request.form['make']
        equipment.model = request.form['model']
        equipment.serial_number = request.form['serial_number']
        equipment.installation_date = datetime.strptime(request.form['installation_date'], '%Y-%m-%d').date() if request.form['installation_date'] else None
        equipment.location = request.form['location']
        equipment.specifications = request.form['specifications']
        equipment.contract_id = request.form['contract_id']
        equipment.status = request.form.get('status', equipment.status)
        
        try:
            db.session.commit()
            flash('Equipment updated successfully.', 'success')
            return redirect(url_for('amc.view_equipment', id=equipment.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating equipment. Please try again.', 'danger')
    
    return render_template('amc/equipment_form.html', equipment=equipment, contracts=contracts, title='Edit Equipment')

@bp.route('/contract/<int:contract_id>/assign_technicians', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_technicians(contract_id):
    contract = AMCContract.query.get_or_404(contract_id)
    form = TechnicianAssignmentForm()
    
    # Get all technicians
    technicians = User.query.filter_by(role='technician').all()
    # Filter technicians based on their existing assignments and contract type
    if contract.contract_type == 'CWAN & CCTV':
        # Get technicians with CWAN & CCTV expertise
        jr_techs = [(t.id, t.full_name) for t in technicians 
                    if not any(a.is_senior for a in t.contract_assignments) and
                    not any(a.contract.contract_type != 'CWAN & CCTV' for a in t.contract_assignments)]
        sr_techs = [(t.id, t.full_name) for t in technicians 
                    if any(a.is_senior for a in t.contract_assignments) and
                    not any(a.contract.contract_type != 'CWAN & CCTV' for a in t.contract_assignments)]
    else:  # Computer and Printers
        # Get technicians with Computer and Printers expertise
        jr_techs = [(t.id, t.full_name) for t in technicians 
                    if not any(a.is_senior for a in t.contract_assignments) and
                    not any(a.contract.contract_type != 'Computer and Printers' for a in t.contract_assignments)]
        sr_techs = [(t.id, t.full_name) for t in technicians 
                    if any(a.is_senior for a in t.contract_assignments) and
                    not any(a.contract.contract_type != 'Computer and Printers' for a in t.contract_assignments)]
    
    # Add unassigned technicians to both lists
    unassigned_techs = [(t.id, f"{t.full_name} (Unassigned)") for t in technicians 
                        if not t.contract_assignments]
    jr_techs.extend(unassigned_techs)
    sr_techs.extend(unassigned_techs)
    
    form.junior_technician.choices = jr_techs
    form.senior_technician.choices = sr_techs
    
    # Pre-select current assignments if they exist
    current_jr = TechnicianAssignment.query.filter_by(contract_id=contract_id, is_senior=False).first()
    current_sr = TechnicianAssignment.query.filter_by(contract_id=contract_id, is_senior=True).first()
    
    if request.method == 'GET':
        if current_jr:
            form.junior_technician.data = current_jr.technician_id
        if current_sr:
            form.senior_technician.data = current_sr.technician_id
    
    if form.validate_on_submit():
        # Remove existing assignments for this contract
        TechnicianAssignment.query.filter_by(contract_id=contract_id).delete()
        
        # Create new assignments
        jr_assignment = TechnicianAssignment(
            technician_id=form.junior_technician.data,
            contract_id=contract_id,
            is_senior=False
        )
        sr_assignment = TechnicianAssignment(
            technician_id=form.senior_technician.data,
            contract_id=contract_id,
            is_senior=True
        )
        
        db.session.add(jr_assignment)
        db.session.add(sr_assignment)
        
        try:
            db.session.commit()
            flash(f'Technicians assigned to contract {contract.contract_number} successfully!', 'success')
            return redirect(url_for('amc.view_contract', id=contract_id))
        except Exception as e:
            db.session.rollback()
            flash('Error assigning technicians. Please try again.', 'danger')
    
    return render_template('amc/assign_technicians.html', form=form, contract=contract)

@bp.route('/contract/<int:contract_id>/view_assignments')
@login_required
def view_assignments(contract_id):
    contract = AMCContract.query.get_or_404(contract_id)
    assignments = TechnicianAssignment.query.filter_by(contract_id=contract_id).all()
    return render_template('amc/view_assignments.html', contract=contract, assignments=assignments)
    equipment = Equipment.query.get_or_404(id)
    contracts = AMCContract.query.filter_by(status='ACTIVE').all()
    
    if request.method == 'POST':
        equipment.name = request.form['name']
        equipment.type = request.form['type']
        equipment.make = request.form['make']
        equipment.model = request.form['model']
        equipment.serial_number = request.form['serial_number']
        equipment.installation_date = datetime.strptime(request.form['installation_date'], '%Y-%m-%d').date() if request.form['installation_date'] else None
        equipment.location = request.form['location']
        equipment.specifications = request.form['specifications']
        equipment.contract_id = request.form['contract_id']
        equipment.status = request.form.get('status', equipment.status)
        
        try:
            db.session.commit()
            flash('Equipment updated successfully.', 'success')
            return redirect(url_for('amc.view_equipment', id=equipment.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating equipment. Please try again.', 'danger')
    
    return render_template('amc/equipment_form.html', equipment=equipment, contracts=contracts, title='Edit Equipment')
