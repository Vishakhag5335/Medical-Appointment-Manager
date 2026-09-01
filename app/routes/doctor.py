from datetime import date as dt_date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.forms.availability import DoctorAvailabilityForm
from app.forms.appointment import ConsultationNotesForm
from app.services.appointment_service import AppointmentService
from app.utils.decorators import doctor_approved_required

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')


def get_current_doctor():
    """Helper to retrieve current authenticated doctor profile."""
    if not current_user.doctor or current_user.doctor.verification_status != 'approved':
        abort(403)
    return current_user.doctor


@doctor_bp.route('/dashboard', methods=['GET'])
@login_required
@doctor_approved_required
def dashboard():
    """Doctor Dashboard overview."""
    doctor = get_current_doctor()
    today = dt_date.today()

    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == today,
        Appointment.status.in_(['Approved', 'Pending', 'Completed'])
    ).order_by(Appointment.appointment_time.asc()).all()

    pending_approvals = Appointment.query.filter_by(
        doctor_id=doctor.id,
        status='Pending'
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date > today,
        Appointment.status == 'Approved'
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).limit(10).all()

    # Unique patients
    patient_ids = db.session.query(Appointment.patient_id).filter_by(doctor_id=doctor.id).distinct().all()
    patient_count = len(patient_ids)

    return render_template(
        'doctor/dashboard.html',
        today_appointments=today_appointments,
        pending_approvals=pending_approvals,
        upcoming_appointments=upcoming_appointments,
        patient_count=patient_count
    )


@doctor_bp.route('/slots', methods=['GET', 'POST'])
@login_required
@doctor_approved_required
def slots():
    """Doctor Availability Slot Management."""
    doctor = get_current_doctor()
    form = DoctorAvailabilityForm()

    if form.validate_on_submit():
        success, result = AppointmentService.create_availability_slot(
            doctor=doctor,
            date_val=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            appointment_type=form.appointment_type.data
        )

        if success:
            flash(f"Availability slot created for {form.date.data.strftime('%Y-%m-%d')} ({form.start_time.data.strftime('%H:%M')} - {form.end_time.data.strftime('%H:%M')}).", 'success')
            return redirect(url_for('doctor.slots'))
        else:
            flash(f"Failed to create slot: {result}", 'danger')

    today = dt_date.today()
    slots_list = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.date >= today
    ).order_by(DoctorAvailability.date.asc(), DoctorAvailability.start_time.asc()).all()

    return render_template('doctor/slots.html', form=form, slots=slots_list)


@doctor_bp.route('/slots/<int:id>/delete', methods=['POST'])
@login_required
@doctor_approved_required
def delete_slot(id):
    """Delete an availability slot."""
    doctor = get_current_doctor()
    slot = db.session.get(DoctorAvailability, id)

    if not slot or slot.doctor_id != doctor.id:
        abort(404)

    try:
        db.session.delete(slot)
        db.session.commit()
        flash('Availability slot deleted successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting slot: {str(e)}', 'danger')

    return redirect(url_for('doctor.slots'))


@doctor_bp.route('/appointments/<int:id>', methods=['GET'])
@login_required
@doctor_approved_required
def appointment_detail(id):
    """View appointment details and patient background info."""
    doctor = get_current_doctor()
    appointment = db.session.get(Appointment, id)

    if not appointment:
        abort(404)

    if appointment.doctor_id != doctor.id:
        abort(403)

    notes_form = ConsultationNotesForm(consultation_notes=appointment.consultation_notes or '')

    return render_template('doctor/appointment_detail.html', appointment=appointment, notes_form=notes_form)


@doctor_bp.route('/appointments/<int:id>/approve', methods=['POST'])
@login_required
@doctor_approved_required
def approve_appointment(id):
    """Approve a pending appointment."""
    doctor = get_current_doctor()
    success, result = AppointmentService.approve_appointment(id, doctor)

    if success:
        flash('Appointment approved successfully.', 'success')
    else:
        flash(f'Approval failed: {result}', 'danger')

    return redirect(request.referrer or url_for('doctor.dashboard'))


@doctor_bp.route('/appointments/<int:id>/reject', methods=['POST'])
@login_required
@doctor_approved_required
def reject_appointment(id):
    """Reject a pending appointment."""
    doctor = get_current_doctor()
    success, result = AppointmentService.reject_appointment(id, doctor)

    if success:
        flash('Appointment rejected.', 'info')
    else:
        flash(f'Rejection failed: {result}', 'danger')

    return redirect(request.referrer or url_for('doctor.dashboard'))


@doctor_bp.route('/appointments/<int:id>/notes', methods=['POST'])
@login_required
@doctor_approved_required
def update_notes(id):
    """Add or update consultation notes."""
    doctor = get_current_doctor()
    appointment = db.session.get(Appointment, id)

    if not appointment or appointment.doctor_id != doctor.id:
        abort(403)

    form = ConsultationNotesForm()
    if form.validate_on_submit():
        try:
            appointment.consultation_notes = form.consultation_notes.data.strip()
            db.session.commit()
            flash('Consultation notes saved successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving notes: {str(e)}', 'danger')

    return redirect(url_for('doctor.appointment_detail', id=appointment.id))
