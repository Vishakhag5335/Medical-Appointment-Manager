import os
import uuid
from flask import current_app
from app.extensions import db
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.medical_report import MedicalReport


ALLOWED_REPORT_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}


class ReportService:
    """Business logic for uploading, managing, and securing access to medical reports."""

    @staticmethod
    def upload_report(uploaded_by_user, patient_id, title, report_type, file_data, notes=None, appointment_id=None):
        """Uploads a medical report document safely with UUID storage."""
        patient = db.session.get(Patient, patient_id)
        if not patient:
            return False, "Patient not found."

        if not file_data or not hasattr(file_data, 'filename') or not file_data.filename:
            return False, "No valid file selected for upload."

        filename = file_data.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext.lstrip('.') not in ALLOWED_REPORT_EXTENSIONS:
            return False, "Only PDF, JPG, JPEG, and PNG files are allowed for medical reports."

        try:
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'medical_reports')
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, unique_filename)
            if hasattr(file_data, 'save'):
                file_data.save(file_path)
            else:
                file_data.seek(0)
                with open(file_path, 'wb') as f:
                    f.write(file_data.read())


            report = MedicalReport(
                patient_id=patient.id,
                appointment_id=appointment_id,
                uploaded_by_id=uploaded_by_user.id,
                title=title.strip(),
                report_type=report_type,
                file_path=unique_filename,
                notes=notes.strip() if notes else None
            )
            db.session.add(report)
            db.session.commit()
            return True, report
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to upload report: {str(e)}"

    @staticmethod
    def can_user_access_report(user, report):
        """Strict RBAC authorization check for accessing medical reports."""
        if not user or not user.is_authenticated:
            return False

        if user.is_admin():
            return True

        if user.is_patient():
            return user.patient is not None and user.patient.id == report.patient_id

        if user.is_doctor():
            if not user.doctor or user.doctor.verification_status != 'approved':
                return False
            # Doctor has access if they have or had an appointment with this patient
            has_appointment = Appointment.query.filter_by(
                doctor_id=user.doctor.id,
                patient_id=report.patient_id
            ).first() is not None
            return has_appointment

        return False
