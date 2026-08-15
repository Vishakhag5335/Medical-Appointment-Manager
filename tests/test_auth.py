import os
import inspect
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.utils.decorators import role_required, doctor_approved_required
from app.utils.security import is_safe_url, validate_password_strength
from flask import Blueprint, jsonify, request


@pytest.fixture
def app():
    """App fixture using TestingConfig with isolated database."""
    app = create_app('testing')

    # Register test blueprint for authorization decorator testing
    test_bp = Blueprint('test_auth_routes', __name__)

    @test_bp.route('/test-admin-only')
    @role_required('admin')
    def admin_only():
        return jsonify({'message': 'Admin Access Granted'})

    @test_bp.route('/test-doctor-only')
    @doctor_approved_required
    def doctor_approved_only():
        return jsonify({'message': 'Approved Doctor Access Granted'})

    @test_bp.route('/test-patient-only')
    @role_required('patient')
    def patient_only():
        return jsonify({'message': 'Patient Access Granted'})

    app.register_blueprint(test_bp)

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner fixture."""
    return app.test_cli_runner()


# 1. App creation
def test_app_creation(app):
    assert app.config['TESTING'] is True


# 2. Patient registration success
def test_patient_registration_success(client, app):
    response = client.post('/auth/register', data={
        'name': 'Valid Patient',
        'email': 'validpatient@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
        'gender': 'female'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='validpatient@example.com').first()
        assert user is not None
        assert user.role == 'patient'
        assert user.patient is not None


# 3. Duplicate email rejection
def test_duplicate_email_rejection(client):
    client.post('/auth/register', data={
        'name': 'Patient One',
        'email': 'dup@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })

    response = client.post('/auth/register', data={
        'name': 'Patient Two',
        'email': 'dup@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })

    assert b'This email address is already registered.' in response.data


# 4. Invalid email rejection
def test_invalid_email_rejection(client):
    response = client.post('/auth/register', data={
        'name': 'Invalid Email User',
        'email': 'invalid-email-format',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })

    assert b'Please enter a valid email address.' in response.data


# 5 & 6. Strong password validation & Weak password rejection
def test_password_validation_rules():
    assert validate_password_strength("StrongPass123!")[0] is True
    assert validate_password_strength("short1!")[0] is False  # Min 8
    assert validate_password_strength("nouppercase123!")[0] is False  # Missing uppercase
    assert validate_password_strength("NOLOWERCASE123!")[0] is False  # Missing lowercase
    assert validate_password_strength("NoDigitsHere!")[0] is False  # Missing digit
    assert validate_password_strength("NoSpecialChar123")[0] is False  # Missing special char


# 7. Patient login success
def test_patient_login_success(client, app):
    client.post('/auth/register', data={
        'name': 'Login User',
        'email': 'userlogin@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })

    response = client.post('/auth/login', data={
        'email': 'userlogin@example.com',
        'password': 'StrongPassword123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back, Login User!' in response.data


# 8. Wrong password rejection
def test_wrong_password_rejection(client):
    client.post('/auth/register', data={
        'name': 'User Wrong Pass',
        'email': 'wrongpass@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })

    response = client.post('/auth/login', data={
        'email': 'wrongpass@example.com',
        'password': 'IncorrectPassword123!'
    })

    assert b'Invalid email or password.' in response.data


# 9. POST logout success
def test_post_logout_success(client):
    client.post('/auth/register', data={
        'name': 'Logout User',
        'email': 'postlogout@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })
    client.post('/auth/login', data={
        'email': 'postlogout@example.com',
        'password': 'StrongPassword123!'
    })

    response = client.post('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data


# 10. GET logout rejection (Method Not Allowed 405)
def test_get_logout_rejected(client):
    client.post('/auth/register', data={
        'name': 'Get Logout User',
        'email': 'getlogout@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })
    client.post('/auth/login', data={
        'email': 'getlogout@example.com',
        'password': 'StrongPassword123!'
    })

    response = client.get('/auth/logout')
    assert response.status_code == 405  # Method Not Allowed


# 11. Unauthenticated protected route
def test_unauthenticated_protected_route(client):
    response = client.get('/test-admin-only', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page.' in response.data


# 12. Patient role authorization
def test_patient_role_authorization(client):
    client.post('/auth/register', data={
        'name': 'Patient Authorization Test',
        'email': 'patientauth@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })
    client.post('/auth/login', data={
        'email': 'patientauth@example.com',
        'password': 'StrongPassword123!'
    })

    # Patient accessing patient route -> 200
    res_pat = client.get('/test-patient-only')
    assert res_pat.status_code == 200

    # Patient accessing admin route -> 403
    res_admin = client.get('/test-admin-only')
    assert res_admin.status_code == 403


# 13, 14, 15, 16. Doctor status authorization (Pending, Approved, Rejected)
def test_doctor_status_authorizations(client, app):
    # Register doctor
    client.post('/auth/register/doctor', data={
        'name': 'Dr. Status Check',
        'email': 'dr.status@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
        'specialization': 'General Medicine',
        'qualification': 'MBBS',
        'license_number': 'LIC-STATUS-100'
    })

    client.post('/auth/login', data={
        'email': 'dr.status@example.com',
        'password': 'StrongPassword123!'
    })

    # 14. Pending doctor accessing approved route -> Redirected to /auth/approval-pending
    res_pending = client.get('/test-doctor-only', follow_redirects=True)
    assert res_pending.status_code == 200
    assert b'Doctor Application Under Review' in res_pending.data

    # Approve doctor in DB
    with app.app_context():
        doc = User.query.filter_by(email='dr.status@example.com').first()
        doc.doctor.verification_status = 'approved'
        db.session.commit()

    # 15. Approved doctor accessing approved route -> 200 OK
    res_approved = client.get('/test-doctor-only')
    assert res_approved.status_code == 200
    assert res_approved.get_json()['message'] == 'Approved Doctor Access Granted'

    # Reject doctor in DB
    with app.app_context():
        doc = User.query.filter_by(email='dr.status@example.com').first()
        doc.doctor.verification_status = 'rejected'
        db.session.commit()

    # 16. Rejected doctor accessing approved route -> 403 Forbidden
    res_rejected = client.get('/test-doctor-only')
    assert res_rejected.status_code == 403


# 17 & 18. Safe local next redirect & External URL rejection
def test_safe_local_next_redirect(client, app):
    client.post('/auth/register', data={
        'name': 'Redirect User',
        'email': 'redirect@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    })

    # 17. Valid local next parameter
    res_valid = client.post('/auth/login?next=/test-patient-only', data={
        'email': 'redirect@example.com',
        'password': 'StrongPassword123!'
    }, follow_redirects=True)
    assert res_valid.status_code == 200
    assert b'Patient Access Granted' in res_valid.data

    client.post('/auth/logout')

    # 18. External URL rejection (should redirect to index /)
    res_external = client.post('/auth/login?next=http://evil.com', data={
        'email': 'redirect@example.com',
        'password': 'StrongPassword123!'
    }, follow_redirects=False)
    assert res_external.status_code == 302
    assert res_external.headers['Location'] == '/'

    # Protocol-relative URL rejection
    res_proto = client.post('/auth/login?next=//evil.com', data={
        'email': 'redirect@example.com',
        'password': 'StrongPassword123!'
    }, follow_redirects=False)
    assert res_proto.status_code == 302
    assert res_proto.headers['Location'] == '/'


# 19. Admin creation CLI
def test_admin_creation_cli(runner, app):
    result = runner.invoke(args=['create-admin', '--name', 'CLI Admin', '--email', 'cliadmin@example.com', '--password', 'CliAdminPass123!'])
    assert 'Successfully created admin account' in result.output

    with app.app_context():
        admin = User.query.filter_by(email='cliadmin@example.com').first()
        assert admin is not None
        assert admin.role == 'admin'


# 20. Verify no hardcoded passwords in source code
def test_no_hardcoded_passwords_in_source():
    from app import cli
    source_code = inspect.getsource(cli)
    assert 'AdminPass123!' not in source_code
    assert 'DoctorPass123!' not in source_code
    assert 'PatientPass123!' not in source_code
