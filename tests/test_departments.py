import pytest
from app import create_app
from app.extensions import db
from app.models.department import Department
from app.models.user import User
from app.models.doctor import Doctor


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_create_department(app):
    """Test department creation and unique name constraint."""
    with app.app_context():
        dept1 = Department(name="Cardiology", description="Heart health")
        db.session.add(dept1)
        db.session.commit()

        fetched = Department.query.filter_by(name="Cardiology").first()
        assert fetched is not None
        assert fetched.description == "Heart health"

        # Duplicate name test
        dept2 = Department(name="Cardiology")
        db.session.add(dept2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


def test_doctor_department_relationship(app):
    """Test linking a doctor to a department."""
    with app.app_context():
        dept = Department(name="Pediatrics", description="Child care")
        user = User(name="Dr. Kid", email="dr.kid@test.com", role="doctor")
        user.set_password("SecurePass123!")
        db.session.add_all([dept, user])
        db.session.flush()

        doc = Doctor(
            user_id=user.id,
            department_id=dept.id,
            specialization="Pediatrics",
            qualification="MD",
            license_number="LIC-PED-1",
            verification_status="approved"
        )
        db.session.add(doc)
        db.session.commit()

        assert doc.department.name == "Pediatrics"
        assert dept.doctors.count() == 1
