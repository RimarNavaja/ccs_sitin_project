from datetime import datetime
from dbhelper import db

class SitInSession(db.Model):
    __tablename__ = 'sit_in_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    computer_number = db.Column(db.String(20), nullable=False)
    purpose = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    
    # Define relationship with User model
    user = db.relationship('User', backref=db.backref('sit_in_sessions', lazy=True))
    
    def __init__(self, user_id, computer_number, purpose, notes=None):
        self.user_id = user_id
        self.computer_number = computer_number
        self.purpose = purpose
        self.notes = notes
        
    def end_session(self):
        """End this sit-in session"""
        self.end_time = datetime.now()
        self.status = 'completed'
        
    def cancel_session(self):
        """Cancel this sit-in session"""
        self.status = 'cancelled'
        
    @classmethod
    def get_active_sessions(cls):
        """Get all active sit-in sessions"""
        return cls.query.filter_by(status='active').all()
    
    @classmethod
    def get_user_sessions(cls, user_id):
        """Get all sit-in sessions for a specific user"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.start_time.desc()).all()
    
    @classmethod
    def get_session_by_id(cls, session_id):
        """Get a specific sit-in session by ID"""
        return cls.query.get(session_id)
