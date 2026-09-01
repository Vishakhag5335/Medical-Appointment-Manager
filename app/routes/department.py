from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.department import Department
from app.models.doctor import Doctor
from app.forms.department import DepartmentForm
from app.utils.decorators import role_required

department_bp = Blueprint('department', __name__, url_prefix='/departments')


@department_bp.route('/', methods=['GET'])
def index():
    """List all departments."""
    departments = Department.query.order_by(Department.name.asc()).all()
    return render_template('department/index.html', departments=departments)


@department_bp.route('/<int:id>', methods=['GET'])
def detail(id):
    """View department details and associated approved doctors."""
    department = db.session.get(Department, id)
    if not department:
        abort(404)
    approved_doctors = Doctor.query.filter_by(department_id=department.id, verification_status='approved').all()
    return render_template('department/detail.html', department=department, doctors=approved_doctors)


@department_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    """Admin endpoint to create a new department."""
    form = DepartmentForm()
    if form.validate_on_submit():
        try:
            dept = Department(
                name=form.name.data.strip(),
                description=form.description.data.strip() if form.description.data else None
            )
            db.session.add(dept)
            db.session.commit()
            flash(f'Department "{dept.name}" created successfully.', 'success')
            return redirect(url_for('department.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating department: {str(e)}', 'danger')

    return render_template('department/create.html', form=form)
