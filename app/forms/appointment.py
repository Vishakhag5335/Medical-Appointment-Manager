from datetime import date as dt_date, datetime
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TimeField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError


class AppointmentBookingForm(FlaskForm):
    """Form for patients to book an appointment."""
    department_id = SelectField('Select Department', coerce=int, validators=[DataRequired(message="Please select a department.")])
    doctor_id = SelectField('Select Doctor', coerce=int, validators=[DataRequired(message="Please select a doctor.")])
    appointment_type = SelectField('Appointment Type', choices=[
        ('In-Person', 'In-Person Consultation'),
        ('Video', 'Video Consultation')
    ], validators=[DataRequired()])
    appointment_date = DateField('Appointment Date', validators=[DataRequired(message="Please select a date.")])
    appointment_time = TimeField('Appointment Time', validators=[DataRequired(message="Please select a time.")])
    slot_id = HiddenField('Slot ID', validators=[Optional()])
    notes = TextAreaField('Reason for Visit / Notes', validators=[Optional()])
    submit = SubmitField('Confirm Appointment Booking')

    def validate_appointment_date(self, field):
        if field.data and field.data < dt_date.today():
            raise ValidationError('Appointment date cannot be in the past.')


class ConsultationNotesForm(FlaskForm):
    """Form for doctors to add or update consultation notes."""
    consultation_notes = TextAreaField('Consultation Notes', validators=[
        DataRequired(message="Consultation notes cannot be empty.")
    ])
    submit = SubmitField('Save Notes')


class AppointmentFilterForm(FlaskForm):
    """Filter form for admin appointment management."""
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed')
    ], validators=[Optional()])
    appointment_type = SelectField('Type', choices=[
        ('', 'All Types'),
        ('In-Person', 'In-Person'),
        ('Video', 'Video')
    ], validators=[Optional()])
    submit = SubmitField('Filter Appointments')
