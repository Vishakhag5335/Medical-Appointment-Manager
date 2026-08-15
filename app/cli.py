import os
import click
from datetime import date
from flask.cli import AppGroup
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.utils.security import validate_password_strength

admin_cli = AppGroup('admin', help='Admin management commands.')


def register_cli_commands(app):
    """Registers custom CLI commands with Flask application."""

    @app.cli.command('create-admin')
    @click.option('--name', prompt='Admin Full Name', help='Admin full name.')
    @click.option('--email', prompt='Admin Email Address', help='Admin email address.')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password.')
    def create_admin(name, email, password):
        """Creates an administrator account."""
        email_clean = email.lower().strip()
        existing_user = User.query.filter_by(email=email_clean).first()
        if existing_user:
            click.echo(click.style(f'Error: User with email {email_clean} already exists.', fg='red'))
            return

        is_valid, errors = validate_password_strength(password)
        if not is_valid:
            click.echo(click.style(f'Error: Password does not meet security requirements: {errors[0]}', fg='red'))
            return

        try:
            admin_user = User(
                name=name.strip(),
                email=email_clean,
                role='admin',
                is_active=True
            )
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            click.echo(click.style(f'Successfully created admin account: {email_clean}', fg='green'))
        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f'Failed to create admin account: {str(e)}', fg='red'))

    @app.cli.command('seed-db')
    def seed_db():
        """Seeds initial development data (1 admin, 1 approved doctor, 1 pending doctor, 1 patient)."""
        click.echo('Seeding database with test records...')

        admin_pass = os.environ.get('SEED_ADMIN_PASSWORD')
        doctor_pass = os.environ.get('SEED_DOCTOR_PASSWORD')
        patient_pass = os.environ.get('SEED_PATIENT_PASSWORD')

        if not admin_pass:
            admin_pass = click.prompt('Enter password for SEED Admin', hide_input=True)
        if not doctor_pass:
            doctor_pass = click.prompt('Enter password for SEED Doctors', hide_input=True)
        if not patient_pass:
            patient_pass = click.prompt('Enter password for SEED Patient', hide_input=True)

        # 1. Seed Admin
        admin = User.query.filter_by(email='admin@medcare.com').first()
        if not admin:
            admin = User(name='System Admin', email='admin@medcare.com', role='admin', is_active=True)
            admin.set_password(admin_pass)
            db.session.add(admin)
            click.echo(' - Created Admin (admin@medcare.com)')

        # 2. Seed Approved Doctor
        doc1_user = User.query.filter_by(email='dr.smith@medcare.com').first()
        if not doc1_user:
            doc1_user = User(name='Dr. Sarah Smith', email='dr.smith@medcare.com', role='doctor', is_active=True)
            doc1_user.set_password(doctor_pass)
            db.session.add(doc1_user)
            db.session.flush()

            doc1_profile = Doctor(
                user_id=doc1_user.id,
                specialization='Cardiology',
                qualification='MD, FACC',
                license_number='MED-1001',
                experience_years=12,
                consultation_fee=150.00,
                bio='Experienced cardiologist specializing in cardiovascular wellness.',
                verification_status='approved'
            )
            db.session.add(doc1_profile)
            click.echo(' - Created Approved Doctor (dr.smith@medcare.com)')

        # 3. Seed Pending Doctor
        doc2_user = User.query.filter_by(email='dr.johnson@medcare.com').first()
        if not doc2_user:
            doc2_user = User(name='Dr. Robert Johnson', email='dr.johnson@medcare.com', role='doctor', is_active=True)
            doc2_user.set_password(doctor_pass)
            db.session.add(doc2_user)
            db.session.flush()

            doc2_profile = Doctor(
                user_id=doc2_user.id,
                specialization='Pediatrics',
                qualification='MBBS, DCH',
                license_number='MED-1002',
                experience_years=5,
                consultation_fee=100.00,
                bio='Dedicated pediatrician.',
                verification_status='pending'
            )
            db.session.add(doc2_profile)
            click.echo(' - Created Pending Doctor (dr.johnson@medcare.com)')

        # 4. Seed Patient
        pat_user = User.query.filter_by(email='patient@medcare.com').first()
        if not pat_user:
            pat_user = User(name='Alice Brown', email='patient@medcare.com', role='patient', is_active=True)
            pat_user.set_password(patient_pass)
            db.session.add(pat_user)
            db.session.flush()

            pat_profile = Patient(
                user_id=pat_user.id,
                date_of_birth=date(1995, 6, 15),
                gender='female',
                blood_group='O+',
                allergies='Penicillin',
                emergency_contact_name='Bob Brown',
                emergency_contact_phone='+1234567890'
            )
            db.session.add(pat_profile)
            click.echo(' - Created Patient (patient@medcare.com)')

        try:
            db.session.commit()
            click.echo(click.style('Database seeding complete!', fg='green'))
        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f'Error seeding database: {str(e)}', fg='red'))
