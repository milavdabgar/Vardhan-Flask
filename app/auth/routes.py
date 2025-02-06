from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'technician':
            return redirect(url_for('main.technician_dashboard'))
        else:  # college_admin
            return redirect(url_for('main.college_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        if not user.is_active:
            flash('Your account is inactive. Please contact administrator.', 'danger')
            return redirect(url_for('auth.login'))
        if user.role != form.role.data:
            flash('Invalid role selected for this account', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user)
        next_page = request.args.get('next')
        
        # Redirect to role-specific dashboard
        if user.role == 'admin':
            return redirect(next_page or url_for('main.admin_dashboard'))
        elif user.role == 'technician':
            return redirect(next_page or url_for('main.technician_dashboard'))
        else:  # college_admin
            return redirect(next_page or url_for('main.college_dashboard'))
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'technician':
            return redirect(url_for('main.technician_dashboard'))
        else:  # college_admin
            return redirect(url_for('main.college_dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            role=form.role.data,
            full_name=form.full_name.data,
            contact_number=form.contact_number.data,
            institution=form.institution.data if form.role.data == 'college_admin' else None,
            is_active=False  # New users need admin approval
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please wait for admin approval to login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)
