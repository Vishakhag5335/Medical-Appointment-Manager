from datetime import datetime, timezone
from app.extensions import db


class DoctorAvailability(db.Model):
    """Doctor availability and appointment slot model."""
    __tablename__ = 'doctor_availabilities'
    __table_args__ = (
        db.CheckConstraint("appointment_type IN ('In-Person', 'Video')", name='ck_availability_type'),
        db.UniqueConstraint('doctor_id', 'date', 'start_time', name='uq_doctor_date_start_time'),
    )

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    appointment_type = db.Column(db.String(20), default='In-Person', nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    doctor = db.relationship('Doctor', backref=db.backref('availabilities', cascade='all, delete-orphan', lazy='dynamic'))

    def __repr__(self):
        return f'<DoctorAvailability id={self.id} doctor_id={self.doctor_id} date={self.date} time={self.start_time}-{self.end_time} available={self.is_available}>'
