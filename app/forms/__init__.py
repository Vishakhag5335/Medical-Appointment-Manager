from app.forms.auth import LoginForm, PatientRegistrationForm, DoctorRegistrationForm
from app.forms.department import DepartmentForm
from app.forms.availability import DoctorAvailabilityForm
from app.forms.appointment import AppointmentBookingForm, ConsultationNotesForm, AppointmentFilterForm
from app.forms.patient import PatientProfileForm
from app.forms.prescription import PrescriptionForm, PrescriptionItemForm
from app.forms.medical_report import MedicalReportForm

__all__ = [
    'LoginForm', 'PatientRegistrationForm', 'DoctorRegistrationForm',
    'DepartmentForm', 'DoctorAvailabilityForm', 'AppointmentBookingForm',
    'ConsultationNotesForm', 'AppointmentFilterForm', 'PatientProfileForm',
    'PrescriptionForm', 'PrescriptionItemForm', 'MedicalReportForm'
]

