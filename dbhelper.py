from flask_sqlalchemy import SQLAlchemy
from flask import request, abort, Flask

app = Flask(__name__)

# Update the database URI with the correct hostname, username, password, and database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1010@localhost/ccs_sitin_project'

db = SQLAlchemy()
db.init_app(app)

class User(db.Model):
    __tablename__ = 'users'  # Ensure the table name matches the schema
    id = db.Column(db.Integer, primary_key=True)
    idno = db.Column(db.String(50), unique=True, nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    midname = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(50), nullable=False)
    yearlevel = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    photo_url = db.Column(db.String(200), nullable=True)
    student_session = db.Column(db.Integer, nullable=False) # Added the student_session column

    @staticmethod
    def verify_credentials(username, password):
        if not username or not password:
            abort(400, description="Missing username or password")
        user = User.query.filter_by(username=username, password=password).first()
        return user is not None

    @staticmethod
    def update_profile_photo(user_id, photo_url):
        user = User.query.get(user_id)
        if user:
            user.photo_url = photo_url
            db.session.commit()
        else:
            abort(404, description="User not found")
    
    def deduct_session(self):
        """Deduct one session from the user's available sessions"""
        if self.student_session > 0:
            self.student_session -= 1
            db.session.commit()
            return True
        return False
    
    def add_session(self, count=1):
        """Add sessions to the user's available sessions"""
        self.student_session += count
        db.session.commit()
        return True
    
    @classmethod
    def get_user_by_id(cls, user_id):
        """Get a user by ID"""
        return cls.query.get(user_id)
    
    @classmethod
    def get_user_by_idno(cls, idno):
        """Get a user by ID number"""
        return cls.query.filter_by(idno=idno).first()

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)
    
    def __init__(self, title, content, priority=0, is_active=True):
        self.title = title
        self.content = content
        self.priority = priority
        self.is_active = is_active
    
    # Added the get_active_announcements method
    @classmethod
    def get_active_announcements(cls):
        """Get all active announcements ordered by priority (highest first) and then by date (newest first)"""
        return cls.query.filter_by(is_active=True).order_by(cls.priority.desc(), cls.created_at.desc()).all()
    
    # Added the get_all_announcements method
    @classmethod
    def get_all_announcements(cls):
        """Get all announcements ordered by priority (highest first) and then by date (newest first)"""
        return cls.query.order_by(cls.priority.desc(), cls.created_at.desc()).all()
    
    @classmethod
    def get_announcement_by_id(cls, id):
        """Get announcement by id"""
        return cls.query.get(id)
    
    def to_dict(self):
        """Convert announcement to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_active': self.is_active,
            'priority': self.priority
        }
