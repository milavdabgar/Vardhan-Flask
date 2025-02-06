from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TelField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[
        ('admin', 'Administrator'),
        ('technician', 'Technician'),
        ('college_admin', 'College IT Admin')
    ], validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('college_admin', 'College IT Admin'),
        ('technician', 'Technician')
    ], validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    contact_number = TelField('Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
    institution = StringField('Institution Name', validators=[Length(max=200)])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_institution(self, institution):
        if self.role.data == 'college_admin' and not institution.data:
            raise ValidationError('Institution name is required for College IT Admin role.')
