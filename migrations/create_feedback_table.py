from flask import Flask
from dbhelper import db
from models.feedback import Feedback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1010@localhost/ccs_sitin_project'
db.init_app(app)

with app.app_context():
    # Create the feedback table if it doesn't exist
    db.create_all()
    print("Feedback table created successfully")
