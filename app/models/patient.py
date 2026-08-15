from datetime import datetime
from app.extensions import db


class Patient(db.Model):
    """Patient profile model linked one-to-one with User."""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    medical_conditions = db.Column(db.Text, nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Patient id={self.id} user_id={self.user_id}>'
