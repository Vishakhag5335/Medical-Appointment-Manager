from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Decorator to enforce role-based access control.
    
    Usage:
        @role_required('admin')
        @role_required('doctor', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def doctor_approved_required(f):
    """Decorator ensuring current user is an approved doctor."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if current_user.role != 'doctor':
            abort(403)

        if not current_user.doctor or current_user.doctor.verification_status != 'approved':
            if current_user.doctor and current_user.doctor.verification_status == 'pending':
                flash('Your doctor account is currently pending admin approval.', 'warning')
                return redirect(url_for('auth.approval_pending'))
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
