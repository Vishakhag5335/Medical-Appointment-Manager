# Medical Appointment & Prescription Manager

A production-ready Flask application designed for managing medical appointments, prescription workflows, and role-based access for **Patients**, **Doctors**, and **Admins**.

---

## Project Structure (Phase 1 & Phase 2 Security Hardened)

```text
medical_appointment_manager/
│
├── app/
│   ├── __init__.py           # Application Factory & Logging & CLI Registration
│   ├── extensions.py         # Flask Extensions (SQLAlchemy, Migrate, Login, WTF, Mail)
│   ├── cli.py                # Custom CLI commands (create-admin, seed-db via env vars)
│   │
│   ├── models/               # SQLAlchemy Models with CheckConstraints
│   │   ├── __init__.py
│   │   ├── user.py           # User model with Werkzeug password hashing & role constraint
│   │   ├── patient.py        # Patient profile model
│   │   └── doctor.py         # Doctor profile model with verification_status constraint
│   │
│   ├── routes/               # Blueprint Routes & Handlers
│   │   ├── __init__.py
│   │   ├── main.py           # Main blueprint (/ & /health endpoint)
│   │   └── auth.py           # Auth blueprint (login, patient/doctor register, POST logout)
│   │
│   ├── forms/                # Flask-WTF Forms & Enhanced Validation
│   │   ├── __init__.py
│   │   └── auth.py           # LoginForm, PatientRegistrationForm, DoctorRegistrationForm
│   │
│   ├── services/             # Business Logic & Utility Services
│   │   └── __init__.py
│   │
│   ├── utils/                # Helper Utilities, Security & Decorators
│   │   ├── __init__.py
│   │   ├── security.py       # is_safe_url() & validate_password_strength()
│   │   └── decorators.py     # @role_required & @doctor_approved_required decorators
│   │
│   ├── templates/            # Jinja2 HTML Templates
│   │   ├── base.html         # Bootstrap 5 Responsive Layout with POST logout form
│   │   ├── auth/             # Authentication Templates
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── doctor_register.html
│   │   │   └── approval_pending.html  # Pending doctor notice page
│   │   └── errors/           # Custom Error Templates (404, 500, 403)
│   │       ├── 404.html
│   │       ├── 500.html
│   │       └── 403.html
│   │
│   └── static/               # Static Web Assets
│       ├── css/style.css
│       └── js/main.js
│
├── migrations/               # Database Migration Scripts (Flask-Migrate / Alembic)
├── uploads/                  # Secure File Upload Storage
├── tests/                    # Pytest Suite
│   ├── __init__.py
│   ├── test_basic.py         # Basic app creation & /health tests
│   └── test_auth.py          # Complete auth, validation, security & role tests
│
├── config.py                 # Development, Production, & Testing Configurations
├── run.py                    # Application Entrypoint
├── requirements.txt          # Python Dependencies
├── .env.example              # Environment Variables Template
├── .env                      # Local Environment Configuration (Untracked)
├── .gitignore                # Git Exclusions
└── README.md                 # Documentation
```

---

## Phase 2 Features & Security Hardening

1. **Role-Based Architecture & Database Constraints**:
   - Centralized `User` model (`patient`, `doctor`, `admin`) with `ck_users_role` database constraint.
   - Profile models (`Patient` and `Doctor`) linked via one-to-one relationships with `ck_doctors_verification_status` constraint.
2. **Strict Security Policies**:
   - **No Hardcoded Passwords**: Seed passwords loaded strictly from environment variables (`SEED_ADMIN_PASSWORD`, `SEED_DOCTOR_PASSWORD`, `SEED_PATIENT_PASSWORD`) or interactive prompts.
   - **CSRF-Protected POST Logout**: `POST /auth/logout` with hidden CSRF token field (`GET /auth/logout` rejected with 405).
   - **Open Redirect Prevention**: `is_safe_url(target)` helper rejecting external domains and protocol-relative URLs (`//evil.com`).
   - **Strong Password Rules**: Enforced minimum 8 characters, maximum 128 characters, uppercase, lowercase, digit, and special character requirements.
   - **SameSite Cookies**: Configured `SESSION_COOKIE_SAMESITE = 'Lax'` and `REMEMBER_COOKIE_SAMESITE = 'Lax'`.
3. **Pending Doctor Workflow**:
   - Doctor registration sets `verification_status = 'pending'`.
   - Pending doctors can authenticate but are redirected to `/auth/approval-pending` and restricted from approved provider features by `@doctor_approved_required`.

---

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL Server (or local SQLite fallback during testing)

### Installation & Setup

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and set local values (including seed passwords):
   ```bash
   cp .env.example .env
   ```

4. **Run Database Migrations**:
   ```bash
   flask db upgrade
   ```

5. **Create Admin / Seed Database**:
   ```bash
   flask create-admin
   ```
   Or seed development data using configured `.env` passwords:
   ```bash
   flask seed-db
   ```

6. **Run the Application**:
   ```bash
   python run.py
   ```
   The app will start at `http://127.0.0.1:5000`.

7. **Run Pytest Test Suite**:
   ```bash
   pytest
   ```
