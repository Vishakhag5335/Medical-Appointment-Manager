from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

REPORT_TYPES = [
    ('Lab Result', 'Lab Result'),
    ('X-Ray', 'X-Ray'),
    ('Blood Test', 'Blood Test'),
    ('Scan', 'Scan / Imaging'),
    ('General Report', 'General Medical Report'),
    ('Other', 'Other')
]


class MedicalReportForm(FlaskForm):
    """Form for uploading medical reports and test results."""
    title = StringField('Report Title / Name', validators=[
        DataRequired(message="Report title is required."),
        Length(min=2, max=150, message="Report title must be between 2 and 150 characters.")
    ])
    report_type = SelectField('Report Type', choices=REPORT_TYPES, validators=[
        DataRequired(message="Report type is required.")
    ])
    file = FileField('Upload File (PDF, JPG, JPEG, PNG)', validators=[
        FileRequired(message="Please select a file to upload."),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF, JPG, JPEG, and PNG files are allowed!')
    ])
    notes = TextAreaField('Report Description / Doctor Notes', validators=[
        Optional(),
        Length(max=1000, message="Notes must not exceed 1000 characters.")
    ])
    submit = SubmitField('Upload Report')
