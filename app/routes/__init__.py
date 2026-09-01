from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.department import department_bp
from app.routes.patient import patient_bp
from app.routes.doctor import doctor_bp
from app.routes.admin import admin_bp

__all__ = ['main_bp', 'auth_bp', 'department_bp', 'patient_bp', 'doctor_bp', 'admin_bp']

