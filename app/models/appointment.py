from datetime import datetime, timezone
from app.extensions import db


class Appointment(db.Model):
    """Appointment core model for tracking patient consultations."""
    __tablename__ = 'appointments'
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed')",
            name='ck_appointment_status'
        ),
        db.CheckConstraint(
            "payment_status IN ('Pending', 'Paid', 'Not Required')",
            name='ck_appointment_payment_status'
        ),
        db.CheckConstraint(
            "appointment_type IN ('In-Person', 'Video')",
            name='ck_appointment_type'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True, index=True)

    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.Time, nullable=False)
    appointment_type = db.Column(db.String(20), default='In-Person', nullable=False)

    status = db.Column(db.String(20), default='Pending', nullable=False, index=True)
    payment_status = db.Column(db.String(20), default='Pending', nullable=False)

    consultation_notes = db.Column(db.Text, nullable=True)
    meeting_link = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('appointments', cascade='all, delete-orphan', lazy='dynamic'))
    doctor = db.relationship('Doctor', backref=db.backref('appointments', cascade='all, delete-orphan', lazy='dynamic'))
    department = db.relationship('Department', backref=db.backref('appointments', lazy='dynamic'))

    def __repr__(self):
        return f'<Appointment id={self.id} patient_id={self.patient_id} doctor_id={self.doctor_id} date={self.appointment_date} status={self.status}>'
