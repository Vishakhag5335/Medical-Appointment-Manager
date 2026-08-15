import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, SelectField, IntegerField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from app.models.user import User
from app.models.doctor import Doctor


class LoginForm(FlaskForm):
    """User Login Form."""
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
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
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=100)])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Register as Patient')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('This email address is already registered.')

    def validate_password(self, field):
        password = field.data
        if not re.search(r"[A-Z]", password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r"[a-z]", password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r"[0-9]", password):
            raise ValidationError('Password must contain at least one digit.')


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
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    specialization = StringField('Specialization', validators=[
        DataRequired(message="Specialization is required."),
        Length(max=100)
    ])
    qualification = StringField('Qualification', validators=[
        DataRequired(message="Qualification is required."),
        Length(max=100)
    ])
    license_number = StringField('Medical License Number', validators=[
        DataRequired(message="Medical license number is required."),
        Length(max=50)
    ])
    experience_years = IntegerField('Years of Experience', validators=[Optional()])
    consultation_fee = DecimalField('Consultation Fee ($)', validators=[Optional()])
    bio = TextAreaField('Professional Bio', validators=[Optional()])
    submit = SubmitField('Submit Doctor Application')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('This email address is already registered.')

    def validate_license_number(self, field):
        if Doctor.query.filter_by(license_number=field.data.strip()).first():
            raise ValidationError('This medical license number is already registered.')

    def validate_password(self, field):
        password = field.data
        if not re.search(r"[A-Z]", password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r"[a-z]", password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r"[0-9]", password):
            raise ValidationError('Password must contain at least one digit.')
