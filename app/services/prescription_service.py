from app.extensions import db
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.prescription import Prescription, PrescriptionItem


class PrescriptionService:
    """Business logic for issuing and retrieving digital prescriptions."""

    @staticmethod
    def create_prescription(doctor, patient_id, appointment_id, diagnosis, advice=None, items_data=None):
        """Creates a digital prescription with medication items."""
        patient = db.session.get(Patient, patient_id)
        if not patient:
            return False, "Patient not found."

        appointment = None
        if appointment_id:
            appointment = db.session.get(Appointment, appointment_id)
            if not appointment or appointment.doctor_id != doctor.id:
                return False, "Appointment not found or unauthorized."

        if not diagnosis or not diagnosis.strip():
            return False, "Diagnosis is required."

        if not items_data or len(items_data) == 0:
            return False, "At least one medication item must be added to the prescription."

        try:
            prescription = Prescription(
                appointment_id=appointment.id if appointment else None,
                patient_id=patient.id,
                doctor_id=doctor.id,
                diagnosis=diagnosis.strip(),
                advice=advice.strip() if advice else None
            )
            db.session.add(prescription)
            db.session.flush()

            for item in items_data:
                med_item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_name=item['medicine_name'].strip(),
                    dosage=item['dosage'].strip(),
                    frequency=item['frequency'].strip(),
                    duration=item['duration'].strip(),
                    instructions=item.get('instructions', '').strip() if item.get('instructions') else None
                )
                db.session.add(med_item)

            # Automatically complete appointment upon issuing prescription
            if appointment and appointment.status == 'Approved':
                appointment.status = 'Completed'

            db.session.commit()
            return True, prescription
        except Exception as e:
            db.session.rollback()
            return False, f"Database error creating prescription: {str(e)}"

    @staticmethod
    def get_patient_prescriptions(patient_id):
        """Retrieves all prescriptions for a specific patient."""
        return Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()

    @staticmethod
    def get_doctor_prescriptions(doctor_id):
        """Retrieves all prescriptions issued by a specific doctor."""
        return Prescription.query.filter_by(doctor_id=doctor_id).order_by(Prescription.created_at.desc()).all()
