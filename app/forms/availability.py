from datetime import date as dt_date
from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, SelectField, SubmitField
from wtforms.validators import DataRequired, ValidationError


class DoctorAvailabilityForm(FlaskForm):
    """Form for doctors to create available appointment slots."""
    date = DateField('Slot Date', validators=[DataRequired(message="Slot date is required.")])
    start_time = TimeField('Start Time', validators=[DataRequired(message="Start time is required.")])
    end_time = TimeField('End Time', validators=[DataRequired(message="End time is required.")])
    appointment_type = SelectField('Consultation Type', choices=[
        ('In-Person', 'In-Person'),
        ('Video', 'Video Consultation')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Availability Slot')

    def validate_date(self, field):
        if field.data and field.data < dt_date.today():
            raise ValidationError('Availability date cannot be in the past.')

    def validate_end_time(self, field):
        if self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError('End time must be strictly after start time.')
