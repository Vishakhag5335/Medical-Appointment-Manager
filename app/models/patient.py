from datetime import datetime, timezone
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def profile_completion_percentage(self):
        """Calculates profile completion percentage based on filled fields."""
        fields = [
            self.date_of_birth,
            self.gender,
            self.blood_group,
            self.allergies,
            self.medical_conditions,
            self.emergency_contact_name,
            self.emergency_contact_phone,
            self.profile_photo
        ]
        filled = sum(1 for f in fields if f is not None and str(f).strip() != '')
        return int(round((filled / len(fields)) * 100))

    def __repr__(self):
        return f'<Patient id={self.id} user_id={self.user_id}>'

