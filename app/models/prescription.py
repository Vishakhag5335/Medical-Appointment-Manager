from datetime import datetime, timezone
from app.extensions import db


class Prescription(db.Model):
    """Prescription model issued by doctors to patients."""
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='SET NULL'), nullable=True, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True)

    diagnosis = db.Column(db.Text, nullable=False)
    advice = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('prescriptions', cascade='all, delete-orphan', lazy='dynamic'))
    doctor = db.relationship('Doctor', backref=db.backref('prescriptions', cascade='all, delete-orphan', lazy='dynamic'))
    appointment = db.relationship('Appointment', backref=db.backref('prescription', uselist=False))
    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan', lazy='joined')

    def __repr__(self):
        return f'<Prescription id={self.id} patient_id={self.patient_id} doctor_id={self.doctor_id}>'


class PrescriptionItem(db.Model):
    """Itemized medication record within a prescription."""
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True)

    medicine_name = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)      # e.g., "500mg", "1 tablet"
    frequency = db.Column(db.String(50), nullable=False)   # e.g., "1-0-1", "Twice daily"
    duration = db.Column(db.String(50), nullable=False)    # e.g., "5 days", "1 week"
    instructions = db.Column(db.String(255), nullable=True) # e.g., "Take after food"

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<PrescriptionItem id={self.id} medicine={self.medicine_name} dosage={self.dosage}>'
