import pytest
from datetime import date, time, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.doctor import Doctor
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
def doctor_user(app):
    with app.app_context():
        user = User(name="Dr. Tester", email="dr.tester@test.com", role="doctor")
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.flush()

        doc = Doctor(
            user_id=user.id,
            specialization="Cardiology",
            qualification="MD",
            license_number="LIC-TEST-99",
            verification_status="approved"
        )
        db.session.add(doc)
        db.session.commit()
        return doc.id


def test_create_availability_slot(app, doctor_user):
    """Test creating doctor availability slot."""
    with app.app_context():
        doc = db.session.get(Doctor, doctor_user)
        future_date = date.today() + timedelta(days=2)
        success, slot = AppointmentService.create_availability_slot(
            doctor=doc,
            date_val=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            appointment_type="In-Person"
        )
        assert success is True
        assert slot.is_available is True
        assert slot.date == future_date


def test_availability_overlap_prevention(app, doctor_user):
    """Test preventing overlapping availability slots."""
    with app.app_context():
        doc = db.session.get(Doctor, doctor_user)
        future_date = date.today() + timedelta(days=2)

        # Slot 1: 10:00 - 11:00
        success1, _ = AppointmentService.create_availability_slot(
            doctor=doc,
            date_val=future_date,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        assert success1 is True

        # Slot 2 (Overlapping: 10:30 - 11:30)
        success2, msg = AppointmentService.create_availability_slot(
            doctor=doc,
            date_val=future_date,
            start_time=time(10, 30),
            end_time=time(11, 30)
        )
        assert success2 is False
        assert "overlaps" in msg.lower()


def test_past_date_slot_prevention(app, doctor_user):
    """Test preventing creation of slots in the past."""
    with app.app_context():
        doc = db.session.get(Doctor, doctor_user)
        past_date = date.today() - timedelta(days=1)

        success, msg = AppointmentService.create_availability_slot(
            doctor=doc,
            date_val=past_date,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        assert success is False
        assert "past" in msg.lower()
