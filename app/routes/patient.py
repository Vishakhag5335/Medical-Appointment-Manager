import os
import uuid
from datetime import date as dt_date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort, jsonify, request, send_from_directory, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.models.prescription import Prescription
from app.models.medical_report import MedicalReport
from app.forms.appointment import AppointmentBookingForm
from app.forms.patient import PatientProfileForm
from app.forms.medical_report import MedicalReportForm
from app.services.appointment_service import AppointmentService
from app.services.prescription_service import PrescriptionService
from app.services.report_service import ReportService
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


@patient_bp.route('/profile', methods=['GET'])
@login_required
@role_required('patient')
def view_profile():
    """View authenticated patient health profile."""
    patient = get_current_patient()
    return render_template('patient/profile.html', patient=patient)


@patient_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def edit_profile():
    """Create or update authenticated patient health profile."""
    patient = get_current_patient()
    form = PatientProfileForm(obj=patient)

    if form.validate_on_submit():
        patient.date_of_birth = form.date_of_birth.data
        patient.gender = form.gender.data if form.gender.data else None
        patient.blood_group = form.blood_group.data if form.blood_group.data else None
        patient.allergies = form.allergies.data.strip() if form.allergies.data else None
        patient.medical_conditions = form.medical_conditions.data.strip() if form.medical_conditions.data else None
        patient.emergency_contact_name = form.emergency_contact_name.data.strip() if form.emergency_contact_name.data else None
        patient.emergency_contact_phone = form.emergency_contact_phone.data.strip() if form.emergency_contact_phone.data else None

        # Handle profile photo upload securely
        photo_file = form.profile_photo.data
        if photo_file and hasattr(photo_file, 'filename') and photo_file.filename:
            filename = photo_file.filename
            ext = os.path.splitext(filename)[1].lower()
            if ext.lstrip('.') in {'jpg', 'jpeg', 'png'}:
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_photos')
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, unique_filename)
                photo_file.save(file_path)
                patient.profile_photo = unique_filename
            else:
                flash('Invalid image file format. Allowed extensions are JPG, JPEG, PNG.', 'danger')
                return render_template('patient/profile_edit.html', form=form, patient=patient)

        db.session.commit()
        flash('Health profile updated successfully!', 'success')
        return redirect(url_for('patient.view_profile'))

    # Pre-populate fields on GET request
    if request.method == 'GET':
        form.date_of_birth.data = patient.date_of_birth
        form.gender.data = patient.gender or ''
        form.blood_group.data = patient.blood_group or ''
        form.allergies.data = patient.allergies
        form.medical_conditions.data = patient.medical_conditions
        form.emergency_contact_name.data = patient.emergency_contact_name
        form.emergency_contact_phone.data = patient.emergency_contact_phone

    return render_template('patient/profile_edit.html', form=form, patient=patient)


@patient_bp.route('/profile/photo/<filename>', methods=['GET'])
@login_required
def profile_photo(filename):
    """Securely serve uploaded patient profile photos."""
    safe_name = os.path.basename(filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_photos')
    file_path = os.path.join(upload_dir, safe_name)
    if not os.path.exists(file_path):
        abort(404)
    return send_from_directory(upload_dir, safe_name)


@patient_bp.route('/prescriptions', methods=['GET'])
@login_required
@role_required('patient')
def prescriptions():
    """List authenticated patient prescription history."""
    patient = get_current_patient()
    prescription_list = PrescriptionService.get_patient_prescriptions(patient.id)
    return render_template('patient/prescriptions.html', prescriptions=prescription_list)


@patient_bp.route('/prescriptions/<int:id>', methods=['GET'])
@login_required
@role_required('patient')
def view_prescription(id):
    """View digital prescription detail (Patient view)."""
    patient = get_current_patient()
    prescription = db.session.get(Prescription, id)

    if not prescription:
        abort(404)

    if prescription.patient_id != patient.id:
        abort(403)

    return render_template('prescription/detail.html', prescription=prescription)


@patient_bp.route('/reports', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def reports():
    """Manage patient medical reports and process new report upload."""
    patient = get_current_patient()
    form = MedicalReportForm()

    if form.validate_on_submit():
        success, result = ReportService.upload_report(
            uploaded_by_user=current_user,
            patient_id=patient.id,
            title=form.title.data,
            report_type=form.report_type.data,
            file_data=form.file.data,
            notes=form.notes.data
        )

        if success:
            flash('Medical report uploaded successfully!', 'success')
            return redirect(url_for('patient.reports'))
        else:
            flash(f'Upload failed: {result}', 'danger')

    report_list = MedicalReport.query.filter_by(patient_id=patient.id).order_by(MedicalReport.created_at.desc()).all()
    return render_template('patient/reports.html', form=form, reports=report_list)


@patient_bp.route('/reports/<int:id>/download', methods=['GET'])
@login_required
def download_report(id):
    """Secure endpoint for downloading medical reports with RBAC validation."""
    report = db.session.get(MedicalReport, id)
    if not report:
        abort(404)

    if not ReportService.can_user_access_report(current_user, report):
        abort(403)

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'medical_reports')
    safe_filename = os.path.basename(report.file_path)
    file_path = os.path.join(upload_dir, safe_filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(upload_dir, safe_filename, as_attachment=True, download_name=f"{report.title}_{safe_filename}")


