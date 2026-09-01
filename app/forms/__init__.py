from app.forms.auth import LoginForm, PatientRegistrationForm, DoctorRegistrationForm
from app.forms.department import DepartmentForm
from app.forms.availability import DoctorAvailabilityForm
from app.forms.appointment import AppointmentBookingForm, ConsultationNotesForm, AppointmentFilterForm

__all__ = [
    'LoginForm', 'PatientRegistrationForm', 'DoctorRegistrationForm',
    'DepartmentForm', 'DoctorAvailabilityForm', 'AppointmentBookingForm',
    'ConsultationNotesForm', 'AppointmentFilterForm'
]

