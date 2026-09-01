# Medical Appointment & Prescription Manager

A modular Flask-based medical appointment and prescription management system currently under development.

Phase 1 and Phase 2 are complete, including the application foundation, secure authentication, role-based access control, patient and doctor registration, and doctor approval workflow.

---

## Project Structure

```text
medical_appointment_manager/
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── cli.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── patient.py
│   │   └── doctor.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── auth.py
│   ├── forms/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── services/
│   │   └── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   └── security.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── doctor_register.html
│   │   │   └── approval_pending.html
│   │   └── errors/
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── main.js
│       └── images/
│
├── migrations/
├── uploads/
├── tests/
│   ├── __init__.py
│   ├── test_basic.py
│   └── test_auth.py
├── config.py
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Features Implemented

### Phase 1: Application Foundation
- Flask Application Factory pattern (`create_app`).
- Extension management (`Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-Login`, `Flask-WTF`, `Flask-Mail`).
- Multi-environment configurations (`DevelopmentConfig`, `ProductionConfig`, `TestingConfig`).
- Rotating file logging setup (`logs/medical_app.log`).
- Custom HTTP error pages (`404.html`, `500.html`, `403.html`).
- System health monitoring endpoint (`/health`).

### Phase 2: Authentication, User Management & Security Hardening
- **User Roles & Database Design**:
  - Centralized `User` model (`patient`, `doctor`, `admin`) with `ck_users_role` database constraint.
  - Linked `Patient` and `Doctor` profile models with `ck_doctors_verification_status` database constraint.
- **Authentication & Validation**:
  - Werkzeug password hashing (`generate_password_hash` / `check_password_hash`).
  - Strong password validation (min 8, max 128 characters, uppercase, lowercase, digit, and special character required).
  - Open redirect protection (`is_safe_url`).
  - CSRF-protected `POST /auth/logout` endpoint (`GET /auth/logout` rejected with HTTP 405).
  - SameSite Lax cookie security (`SESSION_COOKIE_SAMESITE = 'Lax'`, `REMEMBER_COOKIE_SAMESITE = 'Lax'`).
- **Doctor Approval Workflow**:
  - Public doctor registration creates accounts with `verification_status = 'pending'`.
  - Pending doctors can authenticate but are restricted from provider routes via `@doctor_approved_required` and redirected to `/auth/approval-pending`.
- **CLI Commands & Dynamic Seeding**:
  - `flask create-admin`: Interactively creates administrator accounts without hardcoded credentials.
  - `flask seed-db`: Seeds development test accounts reading passwords dynamically from environment variables (`SEED_ADMIN_PASSWORD`, `SEED_DOCTOR_PASSWORD`, `SEED_PATIENT_PASSWORD`).

### Phase 3: Appointment Management Core
- **Department Management**:
  - `Department` model for clinical specialty categorization (`General Medicine`, `Cardiology`, `Dermatology`, `Pediatrics`, `Orthopedics`, `Gynecology`, `Neurology`, `Dentistry`).
  - Unique name enforcement and database relationship linking doctors to departments.
- **Doctor Availability & Slot Publishing**:
  - `DoctorAvailability` model for doctor slot management.
  - Supports `In-Person` and `Video Consultation` appointment types.
  - Overlap validation logic preventing past dates, invalid time ranges (start >= end), and overlapping slots.
- **Appointment Model & Status Lifecycle**:
  - `Appointment` core model linking patients, approved doctors, and departments.
  - Status tracking (`Pending`, `Approved`, `Rejected`, `Cancelled`, `Completed`).
  - Payment status tracking (`Pending`, `Paid`, `Not Required`).
  - Validation enforcing future booking, double-booking prevention, and slot availability updates.
- **Patient Booking & Management Flow**:
  - Patient dashboard showing upcoming consultations, pending requests, and appointment count metrics.
  - Multi-step interactive booking form with department and doctor filtering API.
  - View appointment details and patient cancellation flow with automatic availability slot restoration.
- **Doctor Consultation Management**:
  - Doctor dashboard showing today's consultations, pending booking approvals queue, and upcoming appointments.
  - One-click Approve and Reject actions for pending appointment requests.
  - Ability to add and update clinical consultation notes.
- **Admin Support & Filtering**:
  - Admin dashboard and all-appointments view with multi-criteria filtering by Doctor, Patient, Department, Status, and Appointment Type.
- **Automated Test Coverage**:
  - Unit and integration tests covering department creation, slot publishing, overlap prevention, appointment booking, past date prevention, double-booking prevention, patient cancellation, doctor approvals/rejections, and role authorization.


---

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL Server (or local SQLite fallback during development)

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
   Copy `.env.example` to `.env` and set your local database credentials and seed passwords:
   ```bash
   cp .env.example .env
   ```

4. **Run Database Migrations**:
   ```bash
   flask db upgrade
   ```

5. **Create an Admin Account**:
   To create an administrator account interactively:
   ```bash
   flask create-admin
   ```
   Or seed development test accounts using configured environment variables:
   ```bash
   flask seed-db
   ```

6. **Run the Application**:
   ```bash
   python run.py
   ```
   The server will start at `http://127.0.0.1:5000`.

7. **Run Pytest Test Suite**:
   ```bash
   pytest
   ```
