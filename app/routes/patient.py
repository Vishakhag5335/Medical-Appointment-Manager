from datetime import date as dt_date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.forms.appointment import AppointmentBookingForm
from app.services.appointment_service import AppointmentService
from app.utils.decorators import role_required

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')


def get_current_patient():
    """Helper to get current authenticated patient profile."""
    if not current_user.patient:
        abort(403)
    return current_user.patient


@patient_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('patient')
def dashboard():
    """Patient Dashboard overview."""
    patient = get_current_patient()
    today = dt_date.today()

    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= today,
        Appointment.status.in_(['Pending', 'Approved'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    upcoming_count = len(upcoming_appointments)
    pending_count = len([a for a in upcoming_appointments if a.status == 'Pending'])

    recent_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id
    ).order_by(Appointment.created_at.desc()).limit(5).all()

    return render_template(
        'patient/dashboard.html',
        upcoming_appointments=upcoming_appointments[:5],
        upcoming_count=upcoming_count,
        pending_count=pending_count,
        recent_appointments=recent_appointments
    )


@patient_bp.route('/book', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def book():
    """Patient Appointment Booking Flow."""
    patient = get_current_patient()
    form = AppointmentBookingForm()

    departments = Department.query.order_by(Department.name.asc()).all()
    form.department_id.choices = [(0, '-- Select Department --')] + [(d.id, d.name) for d in departments]

    # Populate doctor choices dynamically or based on form submit
    approved_doctors = Doctor.query.filter_by(verification_status='approved').all()
    form.doctor_id.choices = [(0, '-- Select Doctor --')] + [(d.id, f"{d.user.name} ({d.specialization})") for d in approved_doctors]

    if request.method == 'POST':
        # Handle custom dynamic doctor options validation
        if form.department_id.data and form.department_id.data > 0:
            dept_docs = Doctor.query.filter_by(department_id=form.department_id.data, verification_status='approved').all()
            form.doctor_id.choices = [(0, '-- Select Doctor --')] + [(d.id, f"{d.user.name} ({d.specialization})") for d in dept_docs]

        if form.validate_on_submit():
            if form.department_id.data == 0 or form.doctor_id.data == 0:
                flash('Please select both a department and a doctor.', 'danger')
            else:
                success, result = AppointmentService.book_appointment(
                    patient=patient,
                    doctor_id=form.doctor_id.data,
                    department_id=form.department_id.data,
                    appointment_date=form.appointment_date.data,
                    appointment_time=form.appointment_time.data,
                    appointment_type=form.appointment_type.data,
                    notes=form.notes.data.strip() if form.notes.data else None,
                    slot_id=int(form.slot_id.data) if form.slot_id.data and form.slot_id.data.isdigit() else None
                )

                if success:
                    flash('Appointment booking request submitted successfully! Status: Pending Approval.', 'success')
                    return redirect(url_for('patient.appointments'))
                else:
                    flash(f'Booking failed: {result}', 'danger')

    return render_template('patient/book.html', form=form, departments=departments, doctors=approved_doctors)


@patient_bp.route('/appointments', methods=['GET'])
@login_required
@role_required('patient')
def appointments():
    """List patient upcoming appointments and history."""
    patient = get_current_patient()
    today = dt_date.today()

    upcoming = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= today,
        Appointment.status.in_(['Pending', 'Approved'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    history = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        (Appointment.appointment_date < today) | (Appointment.status.in_(['Completed', 'Cancelled', 'Rejected']))
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

    return render_template('patient/appointments.html', upcoming=upcoming, history=history)


@patient_bp.route('/appointments/<int:id>', methods=['GET'])
@login_required
@role_required('patient')
def appointment_detail(id):
    """View patient appointment details."""
    patient = get_current_patient()
    appointment = db.session.get(Appointment, id)

    if not appointment:
        abort(404)

    # Security check: strict ownership validation
    if appointment.patient_id != patient.id:
        abort(403)

    return render_template('patient/appointment_detail.html', appointment=appointment)


@patient_bp.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
@role_required('patient')
def cancel_appointment(id):
    """Cancel patient appointment."""
    patient = get_current_patient()
    appointment = db.session.get(Appointment, id)

    if not appointment:
        abort(404)

    if appointment.patient_id != patient.id:
        abort(403)

    success, msg = AppointmentService.cancel_appointment(id, current_user)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(url_for('patient.appointments'))


@patient_bp.route('/api/doctors/<int:department_id>', methods=['GET'])
@login_required
def api_get_doctors(department_id):
    """JSON endpoint for fetching doctors by department."""
    doctors = Doctor.query.filter_by(department_id=department_id, verification_status='approved').all()
    result = [{
        'id': d.id,
        'name': d.user.name,
        'specialization': d.specialization,
        'qualification': d.qualification,
        'consultation_fee': str(d.consultation_fee) if d.consultation_fee else 'N/A'
    } for d in doctors]
    return jsonify(result)


@patient_bp.route('/api/slots/<int:doctor_id>', methods=['GET'])
@login_required
def api_get_slots(doctor_id):
    """JSON endpoint for fetching available slots for a doctor."""
    date_str = request.args.get('date')
    date_val = None
    if date_str:
        try:
            date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    slots = AppointmentService.get_available_slots(doctor_id, date_val)
    result = [{
        'id': s.id,
        'date': s.date.strftime('%Y-%m-%d'),
        'start_time': s.start_time.strftime('%H:%M'),
        'end_time': s.end_time.strftime('%H:%M'),
        'appointment_type': s.appointment_type
    } for s in slots]
    return jsonify(result)
