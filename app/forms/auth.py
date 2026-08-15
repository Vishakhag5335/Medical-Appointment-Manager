from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, SelectField, IntegerField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, ValidationError
from app.models.user import User
from app.models.doctor import Doctor
from app.utils.security import validate_password_strength


class LoginForm(FlaskForm):
    """User Login Form."""
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address."),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class PatientRegistrationForm(FlaskForm):
    """Patient Registration Form."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address."),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=100)])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[Optional(), Length(min=7, max=20, message="Phone number must be between 7 and 20 characters.")])
    submit = SubmitField('Register as Patient')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('This email address is already registered.')

    def validate_password(self, field):
        is_valid, errors = validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError(errors[0])

    def validate_date_of_birth(self, field):
        if field.data:
            if field.data >= date.today():
                raise ValidationError('Date of birth must be in the past.')
            if (date.today().year - field.data.year) > 120:
                raise ValidationError('Please enter a valid date of birth.')


class DoctorRegistrationForm(FlaskForm):
    """Doctor Registration Form."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address."),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    specialization = StringField('Specialization', validators=[
        DataRequired(message="Specialization is required."),
        Length(min=2, max=100)
    ])
    qualification = StringField('Qualification', validators=[
        DataRequired(message="Qualification is required."),
        Length(min=2, max=100)
    ])
    license_number = StringField('Medical License Number', validators=[
        DataRequired(message="Medical license number is required."),
        Length(min=3, max=50)
    ])
    experience_years = IntegerField('Years of Experience', validators=[
        Optional(),
        NumberRange(min=0, max=70, message="Years of experience must be between 0 and 70.")
    ])
    consultation_fee = DecimalField('Consultation Fee ($)', validators=[
        Optional(),
        NumberRange(min=0, max=10000, message="Consultation fee must be between $0 and $10,000.")
    ])
    bio = TextAreaField('Professional Bio', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit Doctor Application')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('This email address is already registered.')

    def validate_license_number(self, field):
        if Doctor.query.filter_by(license_number=field.data.strip()).first():
            raise ValidationError('This medical license number is already registered.')

    def validate_password(self, field):
        is_valid, errors = validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError(errors[0])
