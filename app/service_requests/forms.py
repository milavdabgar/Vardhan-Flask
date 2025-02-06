from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class ServiceRequestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    equipment_type = SelectField('Equipment Type', choices=[
        ('computer', 'Computer'),
        ('printer', 'Printer'),
        ('cctv', 'CCTV'),
        ('network', 'Network Equipment'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], validators=[DataRequired()])
    location_details = StringField('Location Details', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Submit Request')

class UpdateTicketForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ])
    comment = TextAreaField('Update Comment', validators=[DataRequired()])
    resolution_notes = TextAreaField('Resolution Notes')
    submit = SubmitField('Update Ticket')
