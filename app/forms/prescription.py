from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class PrescriptionForm(FlaskForm):
    """Form for doctors to enter prescription diagnosis and general advice."""
    diagnosis = TextAreaField('Doctor Diagnosis', validators=[
        DataRequired(message="Diagnosis is required."),
        Length(min=3, max=2000, message="Diagnosis must be between 3 and 2000 characters.")
    ])
    advice = TextAreaField('Clinical Advice / General Instructions', validators=[
        Optional(),
        Length(max=2000, message="Advice must not exceed 2000 characters.")
    ])
    submit = SubmitField('Issue Digital Prescription')


class PrescriptionItemForm(FlaskForm):
    """Form for adding individual medication items to a prescription."""
    medicine_name = StringField('Medicine Name', validators=[
        DataRequired(message="Medicine name is required."),
        Length(min=2, max=150, message="Medicine name must be between 2 and 150 characters.")
    ])
    dosage = StringField('Dosage (e.g., 500mg, 1 tablet)', validators=[
        DataRequired(message="Dosage is required."),
        Length(max=50)
    ])
    frequency = StringField('Frequency (e.g., 1-0-1, Twice daily)', validators=[
        DataRequired(message="Frequency is required."),
        Length(max=50)
    ])
    duration = StringField('Duration (e.g., 5 days, 1 week)', validators=[
        DataRequired(message="Duration is required."),
        Length(max=50)
    ])
    instructions = StringField('Special Instructions (e.g., After meals)', validators=[
        Optional(),
        Length(max=255)
    ])
