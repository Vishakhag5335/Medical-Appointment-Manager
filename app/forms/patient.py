from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import Optional, Length, ValidationError


VALID_BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


class PatientProfileForm(FlaskForm):
    """Patient Health Profile Form for creating and updating medical profile."""
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
    blood_group = SelectField(
        'Blood Group',
        choices=[('', 'Select Blood Group')] + [(bg, bg) for bg in VALID_BLOOD_GROUPS],
        validators=[Optional()]
    )
    allergies = TextAreaField('Allergies & Reactions', validators=[
        Optional(),
        Length(max=1000, message="Allergies information must not exceed 1000 characters.")
    ])
    medical_conditions = TextAreaField('Medical Conditions / History', validators=[
        Optional(),
        Length(max=1000, message="Medical conditions information must not exceed 1000 characters.")
    ])
    emergency_contact_name = StringField('Emergency Contact Name', validators=[
        Optional(),
        Length(max=100, message="Emergency contact name must not exceed 100 characters.")
    ])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[
        Optional(),
        Length(min=7, max=20, message="Emergency contact phone must be between 7 and 20 characters.")
    ])
    profile_photo = FileField('Profile Photo (JPG, JPEG, PNG)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG, JPEG, and PNG images are allowed!')
    ])
    submit = SubmitField('Save Health Profile')

    def validate_date_of_birth(self, field):
        if field.data:
            if field.data >= date.today():
                raise ValidationError('Date of birth must be in the past.')
            if (date.today().year - field.data.year) > 120:
                raise ValidationError('Please enter a valid date of birth.')

    def validate_blood_group(self, field):
        if field.data and field.data not in VALID_BLOOD_GROUPS:
            raise ValidationError('Invalid blood group selected.')
