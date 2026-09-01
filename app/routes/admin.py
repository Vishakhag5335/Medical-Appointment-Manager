from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.department import Department
from app.models.appointment import Appointment
from app.forms.appointment import AppointmentFilterForm
from app.utils.decorators import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('admin')
def dashboard():
    """Admin Dashboard view."""
    pending_doctors = Doctor.query.filter_by(verification_status='pending').all()
    approved_doctors = Doctor.query.filter_by(verification_status='approved').all()
    patients = Patient.query.all()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='Pending').count()

    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        pending_doctors=pending_doctors,
        approved_doctors=approved_doctors,
        patient_count=len(patients),
        total_appointments=total_appointments,
        pending_appointments=pending_appointments,
        recent_appointments=recent_appointments
    )


@admin_bp.route('/appointments', methods=['GET'])
@login_required
@role_required('admin')
def appointments():
    """Admin view all appointments with filters."""
    form = AppointmentFilterForm(request.args, meta={'csrf': False})

    departments = Department.query.order_by(Department.name.asc()).all()
    doctors = Doctor.query.filter_by(verification_status='approved').all()

    form.department_id.choices = [(0, 'All Departments')] + [(d.id, d.name) for d in departments]
    form.doctor_id.choices = [(0, 'All Doctors')] + [(d.id, d.user.name) for d in doctors]

    query = Appointment.query

    if form.department_id.data and form.department_id.data > 0:
        query = query.filter(Appointment.department_id == form.department_id.data)

    if form.doctor_id.data and form.doctor_id.data > 0:
        query = query.filter(Appointment.doctor_id == form.doctor_id.data)

    if form.status.data:
        query = query.filter(Appointment.status == form.status.data)

    if form.appointment_type.data:
        query = query.filter(Appointment.appointment_type == form.appointment_type.data)

    appointments_list = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

    return render_template('admin/appointments.html', form=form, appointments=appointments_list)


@admin_bp.route('/appointments/<int:id>', methods=['GET'])
@login_required
@role_required('admin')
def appointment_detail(id):
    """Admin view appointment details."""
    appointment = db.session.get(Appointment, id)
    if not appointment:
        abort(404)
    return render_template('admin/appointment_detail.html', appointment=appointment)


@admin_bp.route('/doctors/<int:id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_doctor(id):
    """Admin approval of pending doctor registration."""
    doctor = db.session.get(Doctor, id)
    if not doctor:
        abort(404)

    try:
        doctor.verification_status = 'approved'
        db.session.commit()
        flash(f'Doctor account for {doctor.user.name} has been approved.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving doctor: {str(e)}', 'danger')

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/doctors/<int:id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def reject_doctor(id):
    """Admin rejection of pending doctor registration."""
    doctor = db.session.get(Doctor, id)
    if not doctor:
        abort(404)

    try:
        doctor.verification_status = 'rejected'
        db.session.commit()
        flash(f'Doctor account for {doctor.user.name} has been rejected.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting doctor: {str(e)}', 'danger')

    return redirect(url_for('admin.dashboard'))
