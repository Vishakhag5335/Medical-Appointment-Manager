import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.utils.decorators import role_required, doctor_approved_required
from flask import Blueprint, jsonify


@pytest.fixture
def app():
    """App fixture using TestingConfig (in-memory SQLite)."""
    app = create_app('testing')
    
    # Register test blueprint for decorator verification
    test_bp = Blueprint('test', __name__)

    @test_bp.route('/test-admin-only')
    @role_required('admin')
    def admin_only():
        return jsonify({'message': 'Admin Access Granted'})

    @test_bp.route('/test-doctor-only')
    @doctor_approved_required
    def doctor_approved_only():
        return jsonify({'message': 'Approved Doctor Access Granted'})

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


def test_app_creation(app):
    """Test application factory initializes cleanly in testing mode."""
    assert app.config['TESTING'] is True


def test_patient_registration_success(client, app):
    """Test registering a new patient account."""
    response = client.post('/auth/register', data={
        'name': 'Test Patient',
        'email': 'newpatient@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'gender': 'male'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='newpatient@example.com').first()
        assert user is not None
        assert user.role == 'patient'
        assert user.patient is not None
        assert user.check_password('Password123!') is True


def test_duplicate_email_rejection(client):
    """Test registering with an existing email fails validation."""
    client.post('/auth/register', data={
        'name': 'Patient One',
        'email': 'existing@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })

    response = client.post('/auth/register', data={
        'name': 'Patient Two',
        'email': 'existing@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })

    assert b'This email address is already registered.' in response.data


def test_invalid_email_rejection(client):
    """Test registering with invalid email format."""
    response = client.post('/auth/register', data={
        'name': 'Invalid Email User',
        'email': 'not-an-email',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })

    assert b'Please enter a valid email address.' in response.data


def test_weak_password_rejection(client):
    """Test registering with a weak password without uppercase/digit."""
    response = client.post('/auth/register', data={
        'name': 'Weak Password User',
        'email': 'weak@example.com',
        'password': 'weakpassword',
        'confirm_password': 'weakpassword'
    })

    assert b'Password must contain at least one uppercase letter.' in response.data or \
           b'Password must contain at least one digit.' in response.data


def test_password_mismatch_rejection(client):
    """Test registering with mismatching password fields."""
    response = client.post('/auth/register', data={
        'name': 'Mismatch User',
        'email': 'mismatch@example.com',
        'password': 'Password123!',
        'confirm_password': 'Different123!'
    })

    assert b'Passwords must match.' in response.data


def test_patient_login_success(client, app):
    """Test logging in with valid credentials."""
    # Register user first
    client.post('/auth/register', data={
        'name': 'Login Patient',
        'email': 'loginpatient@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })

    # Perform login
    response = client.post('/auth/login', data={
        'email': 'loginpatient@example.com',
        'password': 'Password123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back, Login Patient!' in response.data

    with app.app_context():
        user = User.query.filter_by(email='loginpatient@example.com').first()
        assert user.last_login is not None


def test_wrong_password_rejection(client):
    """Test logging in with wrong password."""
    client.post('/auth/register', data={
        'name': 'Wrong Pass User',
        'email': 'wrongpass@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })

    response = client.post('/auth/login', data={
        'email': 'wrongpass@example.com',
        'password': 'IncorrectPassword1!'
    })

    assert b'Invalid email or password.' in response.data


def test_logout(client):
    """Test logging out an authenticated user."""
    client.post('/auth/register', data={
        'name': 'Logout User',
        'email': 'logout@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })

    client.post('/auth/login', data={
        'email': 'logout@example.com',
        'password': 'Password123!'
    })

    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data


def test_role_based_access_admin_only(client, app):
    """Test @role_required('admin') decorator blocks patients and allows admins."""
    # 1. Register and login as patient
    client.post('/auth/register', data={
        'name': 'Normal Patient',
        'email': 'patient_role@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    client.post('/auth/login', data={
        'email': 'patient_role@example.com',
        'password': 'Password123!'
    })

    # Patient attempts to access admin route -> 403
    res = client.get('/test-admin-only')
    assert res.status_code == 403

    client.get('/auth/logout')

    # 2. Create admin user and login
    with app.app_context():
        admin = User(name='Admin User', email='admin_role@example.com', role='admin', is_active=True)
        admin.set_password('AdminPass123!')
        db.session.add(admin)
        db.session.commit()

    client.post('/auth/login', data={
        'email': 'admin_role@example.com',
        'password': 'AdminPass123!'
    })

    # Admin accesses admin route -> 200
    res_admin = client.get('/test-admin-only')
    assert res_admin.status_code == 200
    assert res_admin.get_json()['message'] == 'Admin Access Granted'


def test_doctor_pending_status_protection(client, app):
    """Test pending doctor cannot access @doctor_approved_required routes until approved."""
    # Register pending doctor
    client.post('/auth/register/doctor', data={
        'name': 'Dr. Pending',
        'email': 'pendingdoc@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'specialization': 'Pediatrics',
        'qualification': 'MD',
        'license_number': 'LIC-9900'
    })

    client.post('/auth/login', data={
        'email': 'pendingdoc@example.com',
        'password': 'Password123!'
    })

    # Pending doctor attempts to access approved-doctor endpoint -> 403
    res_pending = client.get('/test-doctor-only')
    assert res_pending.status_code == 403

    # Approve doctor in DB
    with app.app_context():
        doc_user = User.query.filter_by(email='pendingdoc@example.com').first()
        doc_user.doctor.verification_status = 'approved'
        db.session.commit()
        db.session.remove()

    res_approved = client.get('/test-doctor-only')
    assert res_approved.status_code == 200

def test_admin_creation_cli(runner, app):

    """Test flask create-admin CLI command."""
    result = runner.invoke(args=['create-admin', '--name', 'CLI Admin', '--email', 'cliadmin@example.com', '--password', 'CliAdminPass1!'])
    assert 'Successfully created admin account' in result.output

    with app.app_context():
        admin = User.query.filter_by(email='cliadmin@example.com').first()
        assert admin is not None
        assert admin.role == 'admin'
