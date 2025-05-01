from dbhelper import db
from datetime import datetime

class LabSchedule(db.Model):
    __tablename__ = 'lab_schedules'

    id = db.Column(db.Integer, primary_key=True)
    lab_name = db.Column(db.String(50), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=True) # e.g., 'Monday', 'Tuesday'
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    subject = db.Column(db.String(100), nullable=True)
    instructor = db.Column(db.String(100), nullable=True)
    section = db.Column(db.String(50), nullable=True)
    file_path = db.Column(db.String(512), nullable=True) # Relative path for uploaded schedule files
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_file_upload = db.Column(db.Boolean, default=False) # Flag to distinguish file upload vs manual entry

    def __repr__(self):
        if self.is_file_upload:
            return f'<LabSchedule {self.id}: {self.lab_name} (File)>'
        else:
            return f'<LabSchedule {self.id}: {self.lab_name} - {self.day_of_week} {self.start_time}-{self.end_time}>'

    @classmethod
    def get_active_schedules(cls):
        """Returns all active lab schedules, ordered by lab then day/time."""
        # Basic ordering, can be refined
        return cls.query.filter_by(is_active=True).order_by(cls.lab_name, cls.day_of_week, cls.start_time).all()

    @classmethod
    def get_all_schedules(cls):
        """Returns all lab schedules, ordered by lab then day/time."""
        return cls.query.order_by(cls.lab_name, cls.day_of_week, cls.start_time).all()

    @classmethod
    def get_schedule_by_id(cls, schedule_id):
        """Returns a lab schedule by its ID."""
        return cls.query.get(schedule_id)
