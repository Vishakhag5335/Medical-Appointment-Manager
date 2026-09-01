from datetime import date as dt_date, datetime, timezone
from app.extensions import db
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.availability import DoctorAvailability
from app.models.appointment import Appointment


class AppointmentService:
    """Business logic service for managing availability slots and appointments."""

    @staticmethod
    def create_availability_slot(doctor, date_val, start_time, end_time, appointment_type='In-Person'):
        """Create a new doctor availability slot with overlap validation."""
        today = dt_date.today()
        now_time = datetime.now(timezone.utc).time()

        if date_val < today:
            return False, "Cannot create availability slots in the past."

        if date_val == today and start_time <= now_time:
            return False, "Start time must be in the future."

        if start_time >= end_time:
            return False, "Start time must be strictly before end time."

        # Check for overlapping slots
        existing_slots = DoctorAvailability.query.filter_by(doctor_id=doctor.id, date=date_val).all()
        for slot in existing_slots:
            if (slot.start_time < end_time) and (slot.end_time > start_time):
                return False, f"Time slot ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}) overlaps with existing slot ({slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')})."

        try:
            slot = DoctorAvailability(
                doctor_id=doctor.id,
                date=date_val,
                start_time=start_time,
                end_time=end_time,
                appointment_type=appointment_type,
                is_available=True
            )
            db.session.add(slot)
            db.session.commit()
            return True, slot
        except Exception as e:
            db.session.rollback()
            return False, f"Database error creating slot: {str(e)}"

    @staticmethod
    def get_available_slots(doctor_id, date_val=None, appointment_type=None):
        """Retrieve available future slots for a given doctor."""
        query = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.is_available == True,
            DoctorAvailability.date >= dt_date.today()
        )

        if date_val:
            query = query.filter(DoctorAvailability.date == date_val)
        if appointment_type:
            query = query.filter(DoctorAvailability.appointment_type == appointment_type)

        return query.order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()

    @staticmethod
    def book_appointment(patient, doctor_id, department_id, appointment_date, appointment_time, appointment_type, notes=None, slot_id=None):
        """Book a new appointment enforcing slot validation and double-booking rules."""
        today = dt_date.today()
        now_time = datetime.now(timezone.utc).time()

        if appointment_date < today:
            return False, "Cannot book an appointment for a past date."
        if appointment_date == today and appointment_time <= now_time:
            return False, "Cannot book an appointment for a past time today."

        doctor = db.session.get(Doctor, doctor_id)
        if not doctor or not doctor.is_approved():
            return False, "Selected doctor is not available for booking."

        # Check double booking
        existing_apt = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_(['Pending', 'Approved', 'Completed'])
        ).first()

        if existing_apt:
            return False, "The doctor already has an active appointment at this date and time."

        # Check if slot exists and is available
        slot = None
        if slot_id:
            slot = db.session.get(DoctorAvailability, slot_id)
        else:
            slot = DoctorAvailability.query.filter_by(
                doctor_id=doctor_id,
                date=appointment_date,
                start_time=appointment_time,
                is_available=True
            ).first()

        if slot and not slot.is_available:
            return False, "This slot is no longer available."

        try:
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor_id,
                department_id=department_id or doctor.department_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                appointment_type=appointment_type,
                status='Pending',
                payment_status='Pending',
                consultation_notes=notes
            )
            db.session.add(appointment)

            if slot:
                slot.is_available = False

            db.session.commit()
            return True, appointment
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to book appointment: {str(e)}"

    @staticmethod
    def cancel_appointment(appointment_id, user):
        """Cancel an appointment and restore availability slot if appropriate."""
        appointment = db.session.get(Appointment, appointment_id)
        if not appointment:
            return False, "Appointment not found."

        # Authorization check
        if user.is_patient():
            if not user.patient or appointment.patient_id != user.patient.id:
                return False, "Unauthorized access to this appointment."
        elif user.is_doctor():
            if not user.doctor or appointment.doctor_id != user.doctor.id:
                return False, "Unauthorized access to this appointment."
        elif not user.is_admin():
            return False, "Unauthorized access."

        if appointment.status in ['Completed', 'Cancelled']:
            return False, f"Appointment is already {appointment.status.lower()} and cannot be cancelled."

        try:
            appointment.status = 'Cancelled'
            # Restore availability slot if one exists
            slot = DoctorAvailability.query.filter_by(
                doctor_id=appointment.doctor_id,
                date=appointment.appointment_date,
                start_time=appointment.appointment_time
            ).first()

            if slot:
                slot.is_available = True

            db.session.commit()
            return True, "Appointment cancelled successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error cancelling appointment: {str(e)}"

    @staticmethod
    def approve_appointment(appointment_id, doctor):
        """Approve a pending appointment (Doctor function)."""
        appointment = db.session.get(Appointment, appointment_id)
        if not appointment or appointment.doctor_id != doctor.id:
            return False, "Appointment not found or unauthorized."

        if appointment.status != 'Pending':
            return False, f"Only pending appointments can be approved (current status: {appointment.status})."

        try:
            appointment.status = 'Approved'
            db.session.commit()
            return True, appointment
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to approve appointment: {str(e)}"

    @staticmethod
    def reject_appointment(appointment_id, doctor):
        """Reject a pending appointment (Doctor function)."""
        appointment = db.session.get(Appointment, appointment_id)
        if not appointment or appointment.doctor_id != doctor.id:
            return False, "Appointment not found or unauthorized."

        if appointment.status != 'Pending':
            return False, f"Only pending appointments can be rejected (current status: {appointment.status})."

        try:
            appointment.status = 'Rejected'
            # Restore slot availability
            slot = DoctorAvailability.query.filter_by(
                doctor_id=appointment.doctor_id,
                date=appointment.appointment_date,
                start_time=appointment.appointment_time
            ).first()

            if slot:
                slot.is_available = True

            db.session.commit()
            return True, appointment
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to reject appointment: {str(e)}"
