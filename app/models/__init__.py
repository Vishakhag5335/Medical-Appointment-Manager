from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.availability import DoctorAvailability
from app.models.appointment import Appointment
from app.models.prescription import Prescription, PrescriptionItem
from app.models.medical_report import MedicalReport

__all__ = [
    'User', 'Patient', 'Doctor', 'Department', 'DoctorAvailability',
    'Appointment', 'Prescription', 'PrescriptionItem', 'MedicalReport'
]

