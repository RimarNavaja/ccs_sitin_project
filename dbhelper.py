from flask_sqlalchemy import SQLAlchemy
from flask import request, abort

db = SQLAlchemy()

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

    @staticmethod
    def verify_credentials(username, password):
        if not username or not password:
            abort(400, description="Missing username or password")
        user = User.query.filter_by(username=username, password=password).first()
        return user is not None
