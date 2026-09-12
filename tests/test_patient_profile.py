import os
import io
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor


@pytest.fixture
def app():
    """App fixture using TestingConfig with isolated database."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture."""
    return app.test_client()


@pytest.fixture
def setup_users(app):
    """Fixture providing registered patient, second patient, and doctor users."""
    with app.app_context():
        # Patient 1
        u1 = User(name="Alice Patient", email="alice@test.com", role="patient")
        u1.set_password("PatientPass123!")
        db.session.add(u1)
        db.session.flush()

        p1 = Patient(user_id=u1.id, blood_group="A+")
        db.session.add(p1)

        # Patient 2
        u2 = User(name="Bob Patient", email="bob@test.com", role="patient")
        u2.set_password("PatientPass123!")
        db.session.add(u2)
        db.session.flush()

        p2 = Patient(user_id=u2.id, blood_group="O+")
        db.session.add(p2)

        # Doctor
        u3 = User(name="Dr. Smith", email="smith@test.com", role="doctor")
        u3.set_password("DoctorPass123!")
        db.session.add(u3)
        db.session.flush()

        d1 = Doctor(
            user_id=u3.id,
            specialization="Cardiology",
            qualification="MD",
            license_number="LIC-9999",
            verification_status="approved"
        )
        db.session.add(d1)

        db.session.commit()

        return {
            'patient1_user_id': u1.id,
            'patient1_id': p1.id,
            'patient2_user_id': u2.id,
            'patient2_id': p2.id,
            'doctor_user_id': u3.id
        }


def login(client, email, password):
    """Helper to log in a user."""
    return client.post('/auth/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


# 1. Patient can view their own health profile
def test_patient_can_view_own_profile(client, setup_users):
    login(client, 'alice@test.com', 'PatientPass123!')
    response = client.get('/patient/profile')

    assert response.status_code == 200
    assert b'Alice Patient' in response.data
    assert b'My Health Profile' in response.data
    assert b'A+' in response.data


# 2. Patient can update their own health profile successfully
def test_patient_can_update_own_profile(client, app, setup_users):
    login(client, 'alice@test.com', 'PatientPass123!')
    response = client.post('/patient/profile/edit', data={
        'date_of_birth': '1990-05-15',
        'gender': 'female',
        'blood_group': 'B+',
        'allergies': 'Peanuts, Penicillin',
        'medical_conditions': 'Asthma',
        'emergency_contact_name': 'Jane Doe',
        'emergency_contact_phone': '1234567890'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Health profile updated successfully!' in response.data

    with app.app_context():
        patient = db.session.get(Patient, setup_users['patient1_id'])
        assert patient.gender == 'female'
        assert patient.blood_group == 'B+'
        assert patient.allergies == 'Peanuts, Penicillin'
        assert patient.medical_conditions == 'Asthma'
        assert patient.emergency_contact_name == 'Jane Doe'
        assert patient.emergency_contact_phone == '1234567890'


# 3. Unauthenticated user cannot access profile routes
def test_unauthenticated_cannot_access_profile(client):
    res_view = client.get('/patient/profile', follow_redirects=True)
    assert res_view.status_code == 200
    assert b'Please log in to access this page.' in res_view.data

    res_edit = client.get('/patient/profile/edit', follow_redirects=True)
    assert res_edit.status_code == 200
    assert b'Please log in to access this page.' in res_edit.data


# 4. Patient cannot access another patient's profile & role authorization
def test_patient_cannot_access_another_patient_profile(client, setup_users):
    # Logged in as Patient 1 (Alice)
    login(client, 'alice@test.com', 'PatientPass123!')
    res_view = client.get('/patient/profile')

    assert res_view.status_code == 200
    assert b'Alice Patient' in res_view.data
    assert b'Bob Patient' not in res_view.data  # Cannot see Bob's data

    # Non-patient (Doctor) accessing patient profile -> 403 Forbidden
    client.post('/auth/logout')
    login(client, 'smith@test.com', 'DoctorPass123!')
    res_doctor = client.get('/patient/profile')
    assert res_doctor.status_code == 403


# 5. Invalid blood group is rejected
def test_invalid_blood_group_rejected(client, app, setup_users):
    login(client, 'alice@test.com', 'PatientPass123!')
    response = client.post('/patient/profile/edit', data={
        'blood_group': 'Z+'
    })

    assert response.status_code == 200
    assert b'Not a valid choice' in response.data or b'Invalid blood group' in response.data

    with app.app_context():
        patient = db.session.get(Patient, setup_users['patient1_id'])
        assert patient.blood_group == 'A+'  # Unchanged


# 6. Invalid image/file extension is rejected
def test_invalid_image_file_extension_rejected(client, app, setup_users):
    login(client, 'alice@test.com', 'PatientPass123!')
    fake_exe = (io.BytesIO(b"binary content"), 'malicious.exe')

    response = client.post('/patient/profile/edit', data={
        'profile_photo': fake_exe
    }, content_type='multipart/form-data')

    assert response.status_code == 200
    assert b'Only JPG, JPEG, and PNG' in response.data or b'Invalid image file format' in response.data

    with app.app_context():
        patient = db.session.get(Patient, setup_users['patient1_id'])
        assert patient.profile_photo is None


# 7. Valid profile photo upload succeeds
def test_valid_image_file_upload_succeeds(client, app, setup_users):
    login(client, 'alice@test.com', 'PatientPass123!')
    fake_png = (io.BytesIO(b"\x89PNG\r\n\x1a\nfake_image_data"), 'avatar.png')

    response = client.post('/patient/profile/edit', data={
        'profile_photo': fake_png
    }, content_type='multipart/form-data', follow_redirects=True)

    assert response.status_code == 200
    assert b'Health profile updated successfully!' in response.data

    with app.app_context():
        patient = db.session.get(Patient, setup_users['patient1_id'])
        assert patient.profile_photo is not None
        assert patient.profile_photo.endswith('.png')

        # Clean up created file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_photos', patient.profile_photo)
        if os.path.exists(upload_path):
            os.remove(upload_path)


# 8. Profile completion percentage calculation
def test_profile_completion_percentage(app, setup_users):
    with app.app_context():
        patient = db.session.get(Patient, setup_users['patient1_id'])
        # Only blood_group is set initially -> 1 of 8 fields = 12% or 13%
        assert patient.profile_completion_percentage == 12 or patient.profile_completion_percentage == 13

        patient.gender = 'female'
        patient.allergies = 'None'
        patient.medical_conditions = 'None'
        patient.emergency_contact_name = 'Emergency Person'
        patient.emergency_contact_phone = '9999999999'
        patient.profile_photo = 'test.jpg'

        # 7 of 8 fields set -> 88%
        assert patient.profile_completion_percentage == 88
