import os
import io
import pytest
from datetime import date, time, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.prescription import Prescription, PrescriptionItem
from app.models.medical_report import MedicalReport
from app.services.prescription_service import PrescriptionService
from app.services.report_service import ReportService


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


@pytest.fixture
def seed_data(app):
    with app.app_context():
        dept = Department(name="Cardiology", description="Heart Care")
        db.session.add(dept)

        # Doctor
        doc_user = User(name="Dr. Heart", email="drheart@test.com", role="doctor")
        doc_user.set_password("DoctorPass123!")
        db.session.add(doc_user)
        db.session.flush()

        doctor = Doctor(
            user_id=doc_user.id,
            department_id=dept.id,
            specialization="Cardiology",
            qualification="MD",
            license_number="LIC-7777",
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

        # Patient 2 (Unrelated)
        pat_user2 = User(name="Patient Two", email="pat2@test.com", role="patient")
        pat_user2.set_password("PatientPass123!")
        db.session.add(pat_user2)
        db.session.flush()

        patient2 = Patient(user_id=pat_user2.id, blood_group="B+")
        db.session.add(patient2)

        db.session.commit()

        # Approved Appointment for Patient 1
        apt = Appointment(
            patient_id=patient1.id,
            doctor_id=doctor.id,
            department_id=dept.id,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            appointment_type="In-Person",
            status="Approved",
            payment_status="Pending"
        )
        db.session.add(apt)
        db.session.commit()

        return {
            'doctor_user_id': doc_user.id,
            'doctor_id': doctor.id,
            'patient1_user_id': pat_user1.id,
            'patient1_id': patient1.id,
            'patient2_user_id': pat_user2.id,
            'patient2_id': patient2.id,
            'appointment_id': apt.id
        }


def login(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


# 1. Doctor can issue digital prescription
def test_doctor_issue_prescription_success(client, app, seed_data):
    login(client, 'drheart@test.com', 'DoctorPass123!')

    response = client.post(f"/doctor/appointments/{seed_data['appointment_id']}/prescription", data={
        'diagnosis': 'Hypertension Grade 1',
        'advice': 'Reduce salt intake and monitor BP daily.',
        'medicine_name': ['Amlodipine', 'Aspirin'],
        'dosage': ['5mg', '75mg'],
        'frequency': ['1-0-0', '0-1-0'],
        'duration': ['30 days', '30 days'],
        'instructions': ['Take in morning after food', 'Take after lunch']
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Digital prescription issued successfully!' in response.data or b'Rx #' in response.data

    with app.app_context():
        apt = db.session.get(Appointment, seed_data['appointment_id'])
        assert apt.status == 'Completed'
        assert apt.prescription is not None
        assert apt.prescription.diagnosis == 'Hypertension Grade 1'
        assert len(apt.prescription.items) == 2
        assert apt.prescription.items[0].medicine_name == 'Amlodipine'


# 2. Patient can view their own prescription history & detail view
def test_patient_view_prescriptions(client, app, seed_data):
    # Issue prescription via service first
    with app.app_context():
        doctor = db.session.get(Doctor, seed_data['doctor_id'])
        PrescriptionService.create_prescription(
            doctor=doctor,
            patient_id=seed_data['patient1_id'],
            appointment_id=seed_data['appointment_id'],
            diagnosis='Acute Bronchitis',
            advice='Rest and hydrate.',
            items_data=[{
                'medicine_name': 'Azithromycin',
                'dosage': '500mg',
                'frequency': '1-0-0',
                'duration': '5 days',
                'instructions': 'After breakfast'
            }]
        )

    # Log in as Patient 1
    login(client, 'pat1@test.com', 'PatientPass123!')

    res_list = client.get('/patient/prescriptions')
    assert res_list.status_code == 200
    assert b'Acute Bronchitis' in res_list.data
    assert b'Dr. Heart' in res_list.data

    rx = Prescription.query.filter_by(patient_id=seed_data['patient1_id']).first()
    res_detail = client.get(f'/patient/prescriptions/{rx.id}')
    assert res_detail.status_code == 200
    assert b'Azithromycin' in res_detail.data
    assert b'500mg' in res_detail.data


# 3. Patient cannot access another patient's prescription
def test_patient_cannot_view_another_patient_prescription(client, app, seed_data):
    with app.app_context():
        doctor = db.session.get(Doctor, seed_data['doctor_id'])
        _, rx = PrescriptionService.create_prescription(
            doctor=doctor,
            patient_id=seed_data['patient1_id'],
            appointment_id=seed_data['appointment_id'],
            diagnosis='Migraine',
            items_data=[{'medicine_name': 'Sumatriptan', 'dosage': '50mg', 'frequency': 'As needed', 'duration': '5 days'}]
        )
        rx_id = rx.id

    # Log in as Patient 2 (Bob) who does NOT own this prescription
    login(client, 'pat2@test.com', 'PatientPass123!')

    res_forbidden = client.get(f'/patient/prescriptions/{rx_id}')
    assert res_forbidden.status_code == 403


# 4. Medical report upload success & invalid format rejection
def test_medical_report_upload_and_validation(client, app, seed_data):
    login(client, 'pat1@test.com', 'PatientPass123!')

    # Invalid file extension (.exe) rejected
    fake_exe = (io.BytesIO(b"malicious script"), 'lab_results.exe')
    res_invalid = client.post('/patient/reports', data={
        'title': 'Blood Test',
        'report_type': 'Blood Test',
        'file': fake_exe
    })
    assert b'Only PDF, JPG, JPEG, and PNG' in res_invalid.data

    # Valid PDF upload succeeds
    fake_pdf = (io.BytesIO(b"%PDF-1.4 header content"), 'blood_report.pdf')
    res_valid = client.post('/patient/reports', data={
        'title': 'Lipid Profile Test',
        'report_type': 'Lab Result',
        'file': fake_pdf,
        'notes': 'Normal Cholesterol'
    }, follow_redirects=True)

    assert res_valid.status_code == 200
    assert b'Medical report uploaded successfully!' in res_valid.data

    with app.app_context():
        report = MedicalReport.query.filter_by(patient_id=seed_data['patient1_id']).first()
        assert report is not None
        assert report.title == 'Lipid Profile Test'
        assert report.file_path.endswith('.pdf')


# 5. Secure report download authorization (Patient owner & treating doctor vs unauthorized)
def test_secure_report_download(client, app, seed_data):
    with app.app_context():
        pat_user = db.session.get(User, seed_data['patient1_user_id'])
        file_obj = io.BytesIO(b"%PDF-1.4 ECG DATA")
        file_obj.filename = "ecg.pdf"

        success, report = ReportService.upload_report(
            uploaded_by_user=pat_user,
            patient_id=seed_data['patient1_id'],
            title='ECG Report',
            report_type='Scan',
            file_data=file_obj,
            notes='ECG Normal'
        )
        assert success is True
        report_id = report.id

        # Override file_path to test file reading if created
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'medical_reports')
        os.makedirs(upload_dir, exist_ok=True)
        with open(os.path.join(upload_dir, report.file_path), 'wb') as f:
            f.write(b"%PDF-1.4 ECG DATA")

    # Patient 1 (Owner) can download -> 200
    login(client, 'pat1@test.com', 'PatientPass123!')
    res_owner = client.get(f'/patient/reports/{report_id}/download')
    assert res_owner.status_code == 200
    res_owner.close()

    # Treating Doctor can download -> 200
    client.post('/auth/logout')
    login(client, 'drheart@test.com', 'DoctorPass123!')
    res_doctor = client.get(f'/patient/reports/{report_id}/download')
    assert res_doctor.status_code == 200
    res_doctor.close()

    # Patient 2 (Unauthorized) cannot download -> 403
    client.post('/auth/logout')
    login(client, 'pat2@test.com', 'PatientPass123!')
    res_unauth = client.get(f'/patient/reports/{report_id}/download')
    assert res_unauth.status_code == 403
    res_unauth.close()

    # Cleanup test file safely
    with app.app_context():
        rep = db.session.get(MedicalReport, report_id)
        path = os.path.join(app.config['UPLOAD_FOLDER'], 'medical_reports', rep.file_path)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

