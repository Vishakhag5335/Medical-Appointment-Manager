from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models.department import Department


class DepartmentForm(FlaskForm):
    """Form for creating or editing a medical department."""
    name = StringField('Department Name', validators=[
        DataRequired(message="Department name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    description = TextAreaField('Description', validators=[
        Length(max=500, message="Description must not exceed 500 characters.")
    ])
    submit = SubmitField('Save Department')

    def __init__(self, original_name=None, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, field):
        if self.original_name and field.data.strip().lower() == self.original_name.lower():
            return
        dept = Department.query.filter(Department.name.ilike(field.data.strip())).first()
        if dept:
            raise ValidationError('A department with this name already exists.')
