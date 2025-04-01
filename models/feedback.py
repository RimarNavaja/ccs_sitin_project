from dbhelper import db
from datetime import datetime

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sit_in_sessions.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 rating
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with sit-in session
    session = db.relationship('SitInSession', backref=db.backref('feedback', lazy=True, uselist=False))
    
    @staticmethod
    def get_feedback_for_session(session_id):
        """Get feedback for a specific sit-in session"""
        return Feedback.query.filter_by(session_id=session_id).first()
    
    @staticmethod
    def get_all_feedback():
        """Get all feedback"""
        return Feedback.query.all()
    
    @staticmethod
    def get_feedback_stats():
        """Get feedback statistics"""
        from sqlalchemy import func
        
        # Get average rating
        avg_rating = db.session.query(func.avg(Feedback.rating)).scalar()
        
        # Get count of feedback by rating
        rating_counts = db.session.query(
            Feedback.rating, 
            func.count(Feedback.rating)
        ).group_by(Feedback.rating).all()
        
        # Format rating counts
        rating_distribution = {i: 0 for i in range(1, 6)}
        for rating, count in rating_counts:
            rating_distribution[rating] = count
        
        return {
            'average_rating': float(avg_rating) if avg_rating else 0,
            'rating_distribution': rating_distribution,
            'total_feedback': sum(rating_distribution.values())
        }
