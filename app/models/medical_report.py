from datetime import datetime, timezone
from app.extensions import db


class MedicalReport(db.Model):
    """Medical report model for uploaded diagnostic test results and documents."""
    __tablename__ = 'medical_reports'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='SET NULL'), nullable=True, index=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # Lab Result, X-Ray, Blood Test, Scan, General Report, Other
    file_path = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('medical_reports', cascade='all, delete-orphan', lazy='dynamic'))
    appointment = db.relationship('Appointment', backref=db.backref('medical_reports', lazy='dynamic'))
    uploaded_by = db.relationship('User')

    def __repr__(self):
        return f'<MedicalReport id={self.id} title={self.title} patient_id={self.patient_id}>'
