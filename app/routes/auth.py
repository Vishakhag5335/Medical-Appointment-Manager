from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.forms.auth import LoginForm, PatientRegistrationForm, DoctorRegistrationForm
from app.utils.security import is_safe_url

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User Login Route."""
    if current_user.is_authenticated:
        if current_user.role == 'doctor' and current_user.doctor and current_user.doctor.verification_status == 'pending':
            return redirect(url_for('auth.approval_pending'))
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return render_template('auth/login.html', form=form)

        # Log in the user
        login_user(user, remember=form.remember_me.data)

        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        # Check pending status for doctor accounts
        if user.role == 'doctor' and user.doctor and user.doctor.verification_status == 'pending':
            flash(f'Welcome, {user.name}. Your doctor application is pending administrator approval.', 'info')
            return redirect(url_for('auth.approval_pending'))

        flash(f'Welcome back, {user.name}!', 'success')
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register_patient():
    """Patient Registration Route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = PatientRegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.lower().strip(),
                role='patient',
                is_active=True
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # Flush to obtain user.id

            patient = Patient(
                user_id=user.id,
                date_of_birth=form.date_of_birth.data,
                gender=form.gender.data if form.gender.data else None,
                emergency_contact_name=form.emergency_contact_name.data.strip() if form.emergency_contact_name.data else None,
                emergency_contact_phone=form.emergency_contact_phone.data.strip() if form.emergency_contact_phone.data else None
            )
            db.session.add(patient)
            db.session.commit()

            flash('Patient registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except IntegrityError:
            db.session.rollback()
            flash('An error occurred during registration. An account with this email may already exist.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('Registration failed due to a server error. Please try again.', 'danger')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    """Doctor Registration Route (requires admin approval)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = DoctorRegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.lower().strip(),
                role='doctor',
                is_active=True
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # Flush to obtain user.id

            doctor = Doctor(
                user_id=user.id,
                specialization=form.specialization.data.strip(),
                qualification=form.qualification.data.strip(),
                license_number=form.license_number.data.strip(),
                experience_years=form.experience_years.data,
                consultation_fee=form.consultation_fee.data,
                bio=form.bio.data.strip() if form.bio.data else None,
                verification_status='pending'
            )
            db.session.add(doctor)
            db.session.commit()

            flash('Doctor registration submitted! Your account requires administrator approval before accessing provider features.', 'info')
            return redirect(url_for('auth.login'))

        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. The email address or license number is already registered.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('Doctor registration failed due to a server error. Please try again.', 'danger')

    return render_template('auth/doctor_register.html', form=form)


@auth_bp.route('/approval-pending', methods=['GET'])
@login_required
def approval_pending():
    """Doctor Approval Pending Notice View."""
    if current_user.role != 'doctor' or not current_user.doctor or current_user.doctor.verification_status != 'pending':
        return redirect(url_for('main.index'))
    return render_template('auth/approval_pending.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout Route (CSRF-protected POST request)."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
