from datetime import datetime
from app.extensions import db


class Doctor(db.Model):
    """Doctor profile model linked one-to-one with User."""
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    experience_years = db.Column(db.Integer, nullable=True)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    verification_status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def is_approved(self):
        return self.verification_status == 'approved'

    def is_pending(self):
        return self.verification_status == 'pending'

    def is_rejected(self):
        return self.verification_status == 'rejected'

    def __repr__(self):
        return f'<Doctor id={self.id} user_id={self.user_id} status={self.verification_status}>'
