from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class TechnicianAssignmentForm(FlaskForm):
    junior_technician = SelectField('Junior Technician', validators=[DataRequired()], coerce=int)
    senior_technician = SelectField('Senior Technician', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Assign Technicians')
