# Medical Appointment & Prescription Manager

A production-ready Flask application designed for managing medical appointments, prescription workflows, and role-based access for **Patients**, **Doctors**, and **Admins**.

---

## Project Structure (Phase 1 & Phase 2 Complete)

```text
medical_appointment_manager/
│
├── app/
│   ├── __init__.py           # Application Factory & Logging & CLI Registration
│   ├── extensions.py         # Flask Extensions (SQLAlchemy, Migrate, Login, WTF, Mail)
│   ├── cli.py                # Custom CLI commands (create-admin, seed-db)
│   │
│   ├── models/               # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── user.py           # User model with Werkzeug password hashing & Flask-Login
│   │   ├── patient.py        # Patient profile model
│   │   └── doctor.py         # Doctor profile model with verification status
│   │
│   ├── routes/               # Blueprint Routes & Handlers
│   │   ├── __init__.py
│   │   ├── main.py           # Main blueprint (/ & /health endpoint)
│   │   └── auth.py           # Auth blueprint (login, patient/doctor register, logout)
│   │
│   ├── forms/                # Flask-WTF Forms & Custom Validation
│   │   ├── __init__.py
│   │   └── auth.py           # LoginForm, PatientRegistrationForm, DoctorRegistrationForm
│   │
│   ├── services/             # Business Logic & Utility Services
│   │   └── __init__.py
│   │
│   ├── utils/                # Helper Utilities & Decorators
│   │   ├── __init__.py
│   │   └── decorators.py     # @role_required & @doctor_approved_required decorators
│   │
│   ├── templates/            # Jinja2 HTML Templates
│   │   ├── base.html         # Bootstrap 5 Responsive Layout with dynamic navigation
│   │   ├── auth/             # Authentication Templates
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── doctor_register.html
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
│   └── test_auth.py          # Authentication, validation, and role-authorization tests
│
├── config.py                 # Development, Production, & Testing Configurations
├── run.py                    # Application Entrypoint
├── requirements.txt          # Python Dependencies
├── .env.example              # Environment Variables Template
├── .env                      # Local Environment Configuration
├── .gitignore                # Git Exclusions
└── README.md                 # Documentation
```

---

## Phase 2 Features Implemented

1. **Role-Based User Architecture**: Centralized `User` model supporting `patient`, `doctor`, and `admin` roles, linked to dedicated `Patient` and `Doctor` profile tables via one-to-one relationships.
2. **Secure Hashing & Sessions**: Werkzeug `generate_password_hash` & `check_password_hash` with `Flask-Login` session management and HttpOnly cookies.
3. **Patient & Doctor Registration**:
   - Patient registration creates active patient accounts directly inside safe database transactions.
   - Doctor registration requires administrator approval (`verification_status='pending'`).
4. **Role & Approval Protection**:
   - Reusable `@role_required(*roles)` authorization decorator.
   - Reusable `@doctor_approved_required` decorator ensuring pending/rejected doctors cannot access approved doctor features.
5. **CLI Administration Commands**:
   - `flask create-admin`: Interactively or via flags creates administrator accounts.
   - `flask seed-db`: Seeds initial development data (1 admin, 1 approved doctor, 1 pending doctor, 1 patient).

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
   Copy `.env.example` to `.env` and adjust database credentials as needed:
   ```bash
   cp .env.example .env
   ```

4. **Run Database Migrations**:
   ```bash
   flask db upgrade
   ```

5. **Create an Admin Account**:
   ```bash
   flask create-admin --name "System Admin" --email "admin@medcare.com" --password "SecureAdmin123!"
   ```
   Or seed development data:
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
