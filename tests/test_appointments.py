import pytest
from datetime import date, time, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.services.appointment_service import AppointmentService


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def seed_data(app):
    """Seed patient, doctor, and department for appointment tests."""
    with app.app_context():
        dept = Department(name="General Medicine", description="Primary Care")
        db.session.add(dept)

        # Doctor
        doc_user = User(name="Dr. House", email="house@test.com", role="doctor")
        doc_user.set_password("DoctorPass123!")
        db.session.add(doc_user)
        db.session.flush()

        doctor = Doctor(
            user_id=doc_user.id,
            department_id=dept.id,
            specialization="Diagnostics",
            qualification="MD",
            license_number="LIC-8888",
            verification_status="approved"
        )
        db.session.add(doctor)

        # Patient 1
        pat_user1 = User(name="Patient One", email="pat1@test.com", role="patient")
        pat_user1.set_password("PatientPass123!")
        db.session.add(pat_user1)
        db.session.flush()

        patient1 = Patient(user_id=pat_user1.id, blood_group="A+")
        db.session.add(patient1)

        # Patient 2
        pat_user2 = User(name="Patient Two", email="pat2@test.com", role="patient")
        pat_user2.set_password("PatientPass123!")
        db.session.add(pat_user2)
        db.session.flush()

        patient2 = Patient(user_id=pat_user2.id, blood_group="B+")
        db.session.add(patient2)

        db.session.commit()

        return {
            'dept_id': dept.id,
            'doctor_id': doctor.id,
            'doctor_user_id': doc_user.id,
            'patient1_id': patient1.id,
            'patient1_user_id': pat_user1.id,
            'patient2_id': patient2.id,
            'patient2_user_id': pat_user2.id
        }


def test_book_appointment_success(app, seed_data):
    """Test successful patient appointment booking."""
    with app.app_context():
        patient = db.session.get(Patient, seed_data['patient1_id'])
        future_date = date.today() + timedelta(days=3)

        success, apt = AppointmentService.book_appointment(
            patient=patient,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=future_date,
            appointment_time=time(14, 0),
            appointment_type="In-Person",
            notes="General checkup"
        )

        assert success is True
        assert apt.status == 'Pending'
        assert apt.patient_id == patient.id
        assert apt.doctor_id == seed_data['doctor_id']


def test_past_date_booking_prevention(app, seed_data):
    """Test prevention of past date appointment booking."""
    with app.app_context():
        patient = db.session.get(Patient, seed_data['patient1_id'])
        past_date = date.today() - timedelta(days=1)

        success, msg = AppointmentService.book_appointment(
            patient=patient,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=past_date,
            appointment_time=time(10, 0),
            appointment_type="In-Person"
        )

        assert success is False
        assert "past" in msg.lower()


def test_double_booking_prevention(app, seed_data):
    """Test double booking prevention for the same doctor and time slot."""
    with app.app_context():
        patient1 = db.session.get(Patient, seed_data['patient1_id'])
        patient2 = db.session.get(Patient, seed_data['patient2_id'])
        future_date = date.today() + timedelta(days=4)
        apt_time = time(11, 0)

        # First booking succeeds
        success1, _ = AppointmentService.book_appointment(
            patient=patient1,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=future_date,
            appointment_time=apt_time,
            appointment_type="Video"
        )
        assert success1 is True

        # Second booking at same date/time fails
        success2, msg = AppointmentService.book_appointment(
            patient=patient2,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=future_date,
            appointment_time=apt_time,
            appointment_type="Video"
        )
        assert success2 is False
        assert "already" in msg.lower()


def test_patient_cancel_appointment(app, seed_data):
    """Test patient cancelling their own appointment."""
    with app.app_context():
        patient1 = db.session.get(Patient, seed_data['patient1_id'])
        pat_user1 = db.session.get(User, seed_data['patient1_user_id'])
        future_date = date.today() + timedelta(days=5)

        success_book, apt = AppointmentService.book_appointment(
            patient=patient1,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=future_date,
            appointment_time=time(9, 30),
            appointment_type="In-Person"
        )
        assert success_book is True

        success_cancel, msg = AppointmentService.cancel_appointment(apt.id, pat_user1)
        assert success_cancel is True
        assert apt.status == 'Cancelled'


def test_unauthorized_cancellation_prevention(app, seed_data):
    """Test preventing a patient from cancelling another patient's appointment."""
    with app.app_context():
        patient1 = db.session.get(Patient, seed_data['patient1_id'])
        pat_user2 = db.session.get(User, seed_data['patient2_user_id'])
        future_date = date.today() + timedelta(days=6)

        _, apt = AppointmentService.book_appointment(
            patient=patient1,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=future_date,
            appointment_time=time(15, 0),
            appointment_type="In-Person"
        )

        success_cancel, msg = AppointmentService.cancel_appointment(apt.id, pat_user2)
        assert success_cancel is False
        assert "unauthorized" in msg.lower()


def test_doctor_approve_and_reject(app, seed_data):
    """Test doctor approving and rejecting pending appointments."""
    with app.app_context():
        patient1 = db.session.get(Patient, seed_data['patient1_id'])
        doctor = db.session.get(Doctor, seed_data['doctor_id'])
        future_date = date.today() + timedelta(days=7)

        # Booking 1 (Approve test)
        _, apt1 = AppointmentService.book_appointment(
            patient=patient1,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=future_date,
            appointment_time=time(10, 0),
            appointment_type="In-Person"
        )
        success_app, _ = AppointmentService.approve_appointment(apt1.id, doctor)
        assert success_app is True
        assert apt1.status == 'Approved'

        # Booking 2 (Reject test)
        _, apt2 = AppointmentService.book_appointment(
            patient=patient1,
            doctor_id=seed_data['doctor_id'],
            department_id=seed_data['dept_id'],
            appointment_date=future_date,
            appointment_time=time(11, 0),
            appointment_type="Video"
        )
        success_rej, _ = AppointmentService.reject_appointment(apt2.id, doctor)
        assert success_rej is True
        assert apt2.status == 'Rejected'
