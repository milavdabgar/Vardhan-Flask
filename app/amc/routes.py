from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import AMCContract, Equipment
from app.decorators import admin_required
from app.amc import bp
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
