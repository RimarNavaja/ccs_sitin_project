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
    lab_points = db.Column(db.Integer, default=0) #Added the lab_points column

    @staticmethod
    def verify_credentials(username, password):
        if not username or not password:
            abort(400, description="Missing username or password")
        user = User.query.filter_by(username=username, password=password).first()
        return user is not None

    @staticmethod
    def update_profile_photo(user_id, photo_url):
        user = db.session.get(User, user_id)
        if user:
            user.photo_url = photo_url
            db.session.commit()
        else:
            abort(404, description="User not found")
    
    # reset student sessions and points
    @staticmethod
    def reset_session_count(user_id):
        """Reset session count for a user (DOES NOT COMMIT)"""
        user = User.query.get(user_id)
        if user:
            if user.course in ['BSIT', 'BSCS', 'BSIS']:
                user.student_session = 30
            else:
                user.student_session = 15
         # REMOVED COMMIT
        else:
         # Consider raising an error instead of aborting if called within a larger transaction
            raise ValueError(f"User not found with ID: {user_id}")
    
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
        return db.session.get(cls, user_id)
    
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
        return db.session.get(cls, id)
    
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

class ComputerStatus(db.Model):
    __tablename__ = 'computer_status'
    id = db.Column(db.Integer, primary_key=True)
    lab_name = db.Column(db.String(50), nullable=False)
    pc_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available') # 'available', 'used', 'maintenance'
    current_session_id = db.Column(db.Integer, db.ForeignKey('sit_in_sessions.id', ondelete='SET NULL'), nullable=True)
    last_updated = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Define the relationship (optional but good practice)
    current_session = db.relationship('SitInSession', backref='computer_used', foreign_keys=[current_session_id])

    __table_args__ = (db.UniqueConstraint('lab_name', 'pc_number', name='unique_lab_pc'),)

    def __repr__(self):
        return f'<ComputerStatus Lab: {self.lab_name} PC: {self.pc_number} Status: {self.status}>'

    @staticmethod
    def get_computers_by_lab():
        """Fetches all computers grouped by lab."""
        computers = ComputerStatus.query.order_by(ComputerStatus.lab_name, ComputerStatus.pc_number).all()
        labs_data = {}
        for comp in computers:
            if comp.lab_name not in labs_data:
                labs_data[comp.lab_name] = []
            labs_data[comp.lab_name].append(comp)
        return labs_data

    @staticmethod
    def update_status_bulk(computer_ids, new_status):
        """Updates the status for a list of computer IDs."""
        if not computer_ids:
            return 0
        # Validate status
        valid_statuses = ['available', 'used', 'maintenance']
        if new_status not in valid_statuses:
            raise ValueError("Invalid status provided.")

        # Update logic
        query = ComputerStatus.query.filter(ComputerStatus.id.in_(computer_ids))

        # When marking as 'available', clear the session ID
        if new_status == 'available':
            updated_count = query.update({
                ComputerStatus.status: new_status,
                ComputerStatus.current_session_id: None
            }, synchronize_session=False)
        else:
            # For 'used' or 'maintenance', just update status.
            # Linking to session_id should happen when a session starts.
            updated_count = query.update({
                ComputerStatus.status: new_status
            }, synchronize_session=False)

        db.session.commit()
        return updated_count
