from datetime import datetime
from dbhelper import db

class SitInSession(db.Model):
    __tablename__ = 'sit_in_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    purpose = db.Column(db.String(100), nullable=False)
    lab = db.Column(db.String(10))
    notes = db.Column(db.Text)
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    notified = db.Column(db.Boolean, default=False)  # For notification badge
    
    # Define relationship with User model
    user = db.relationship('User', backref=db.backref('sit_in_sessions', lazy=True))
    
    # Update the __init__ method of SitInSession to accept start_time and status as keyword arguments
    def __init__(self, user_id, purpose, lab=None, notes=None, start_time=None, status=None, notified=False):
        self.user_id = user_id
        self.purpose = purpose
        self.lab = lab
        self.notes = notes
        if start_time is not None:
            self.start_time = start_time
        if status is not None:
            self.status = status
        self.notified = notified
    
    def end_session(self):
        """End the current sit-in session"""
        self.end_time = datetime.now()
        self.status = 'completed'
        return self
    
    def cancel_session(self):
        """Cancel this sit-in session"""
        self.status = 'cancelled'
        
    @property
    def student_id(self):
        """Alias for user_id to support code expecting student_id."""
        return self.user_id

    @staticmethod
    def get_session_by_id(session_id):
        """Get a sit-in session by ID"""
        return SitInSession.query.get(session_id)
    
    @staticmethod
    def get_active_sessions():
        """Get all active sit-in sessions"""
        return SitInSession.query.filter_by(status='active').order_by(SitInSession.start_time.desc()).all()
    
    @staticmethod
    def get_user_sessions(user_id):
        """Get all sit-in sessions for a specific user"""
        return SitInSession.query.filter_by(user_id=user_id).order_by(SitInSession.start_time.desc()).all()
    
    @staticmethod
    def get_active_sessions_count():
        """Get the count of active sit-in sessions"""
        return SitInSession.query.filter_by(status='active').count()
    
    @staticmethod
    def get_today_sessions():
        """Get all sit-in sessions for today"""
        today = datetime.now().date()
        return SitInSession.query.filter(
            db.func.date(SitInSession.start_time) == today
        ).order_by(SitInSession.start_time.desc()).all()
    
    @staticmethod
    def user_has_active_session(user_id):
        """Check if a user has any active sessions"""
        return SitInSession.query.filter_by(user_id=user_id, status='active').first() is not None

    @staticmethod
    def has_feedback(session_id):
        """Check if feedback exists for a session"""
        from models.feedback import Feedback
        return Feedback.query.filter_by(session_id=session_id).first() is not None

    @staticmethod
    def get_recent_activities(limit=3):
        """Get recent sit-in activities (both active and completed)"""
        return SitInSession.query.filter(
            SitInSession.status.in_(['active', 'completed'])
        ).order_by(
            SitInSession.start_time.desc()
        ).limit(limit).all()

