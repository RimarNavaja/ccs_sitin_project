from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    url_for,
    jsonify
)
from werkzeug.utils import secure_filename
import os
from dbhelper import db, User, Announcement
from datetime import timedelta, datetime
from models.sit_in_session import SitInSession

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1010@localhost/ccs_sitin_project' 
# username - root password - 1010/@Rimar097851 database - ccs_sitin_project/csssitinproject
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = './static/src/images/userphotos'
db.init_app(app)

with app.app_context():
    db.create_all()  # Ensure the tables are created

@app.route("/login",  methods=["GET", "POST"])
def login() -> None:
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if User.verify_credentials(username, password):
            # Set session lifetime based on remember_me checkbox
            remember_me = 'remember_me' in request.form
            session.permanent = remember_me  # Make the session permanent if remember_me is checked
            if remember_me:
                # Set session to expire after 30 days
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                # Default session timeout (browser session)
                app.permanent_session_lifetime = timedelta(hours=1)
                
            session['user'] = username
            flash("Successfully logged in") # temporary message
            return redirect(url_for('dashboard')) # redirect to dashboard
        else:
            flash("Invalid username or password")
            return redirect(url_for('login'))
    return render_template("login.html")

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    flash("Successfully signed out")
    return redirect(url_for('login'))

@app.route("/returntologin", methods=["GET","POST"])
def returntologin():
    return redirect(url_for('login'))



@app.route("/register", methods=["GET", "POST"])
# 
# Handle user registration.
# GET: Render the registration form.
# POST: Process the registration form data.
#     - Validate form fields.
#     - Check for missing fields.
#     - Ensure passwords match.
#     - Check for existing user with the same idno, email, or username.
#     - Add new user to the database.
#     - Flash appropriate messages for errors or success.
# Returns:
#     None
#
def register() -> None:
    if request.method == "POST":
        if not request.form:
            return redirect(url_for('register'))

        missing_fields = [field for field in [
            'idno', 'lastname', 'firstname', 'midname', 'course',
            'yearlevel', 'email', 'username', 'password', 'confirm_password'
        ] if field not in request.form]

        if missing_fields:
            flash(f"Missing form fields: {', '.join(missing_fields)}", "error")
            return redirect(url_for('register'))

        try:
            idno = request.form['idno']
            lastname = request.form['lastname']
            firstname = request.form['firstname']
            midname = request.form['midname']
            course = request.form['course'].upper()
            yearlevel = request.form['yearlevel']
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            
            # Check if do not passwords match render_template and retain the form data
            if password != confirm_password:
                flash("Passwords do not match")
                return render_template("register.html", form=request.form.to_dict())
            
            #  Check for existing user with the same idno, email, or username
            if User.query.filter_by(idno=idno).first():
                flash("ID Number already exists")
                return render_template("register.html", form=request.form.to_dict())
            if User.query.filter_by(email=email).first():
                flash("Email already exists")
                return render_template("register.html", form=request.form.to_dict())
            # if User.query.filter_by(username=username).first():
            #     flash("Username already exists")
            #     return render_template("register.html", form=request.form.to_dict())

            # Set student session based on course 30 session(how many times they will sit-in) for BSIT and BSCS, 15 session (how many times they will sit-in) for others
            student_session = 30 if course in ['BSIT', 'BSCS', 'Bachelor of Science in Information Technology', 'Bachelor of Science Computer Science'] else 15

            new_user = User(
                idno=idno,
                lastname=lastname,
                firstname=firstname,
                midname=midname,
                course=course,
                yearlevel=yearlevel,
                email=email,
                username=username,
                password=password,
                student_session=student_session
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!")
            return redirect(url_for('returntologin'))
        except KeyError as e:
            flash(f"Missing form field: {e}")
            return redirect(url_for('register'))
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    announcements = Announcement.get_active_announcements()
    return render_template("dashboard.html", user=user, announcements=announcements)

@app.route("/lab_rules")
def lab_rules():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    return render_template("labrules.html", user=user)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    return render_template("profile.html", user=user)



@app.route("/edit_profile", methods=["POST"])
def edit_profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    # Update user ID number
    # user.idno = request.form['idno']

    user.firstname = request.form['firstname']
    user.midname = request.form['midname']
    user.lastname = request.form['lastname']
    user.course = request.form['course']
    user.yearlevel = request.form['yearlevel']
    user.email = request.form['email']
    user.username = request.form['username']
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename != '':
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            User.update_profile_photo(user.id, photo_path)
    if request.form['password'] and request.form['confirm_password']:
        if request.form['password'] == request.form['confirm_password']:
            if User.verify_credentials(user.username, request.form['old_password']):
                user.password = request.form['password']
            else:
                flash("Old password is incorrect")
                return redirect(url_for('profile'))
        else:
            flash("Passwords do not match")
            return redirect(url_for('profile'))
    db.session.commit()
    flash("Profile updated successfully")
    return redirect(url_for('profile'))

@app.route("/return_to_index", methods=["GET","POST"])
def return_to_index():
    return redirect("/")

@app.route("/")
def index() -> None:
    return render_template("index.html",pagetitle = "CCS Sit-in")

# Admin routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login() -> None:
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        # In a real implementation, check against admin credentials
        # For now, we'll use placeholder credentials
        if username == "admin" and password == "admin123":
            # Set session
            session['admin'] = username
            session.permanent = True
            app.permanent_session_lifetime = timedelta(hours=2)
            flash("Admin login successful")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials")
            return redirect(url_for('admin_login'))
    return render_template("admin/login.html")

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin', None)
    flash("Admin signed out successfully")
    return redirect(url_for('admin_login'))

@app.route("/admin/dashboard")
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Get announcement stats
    total_announcements = Announcement.query.count()
    # Counts the active announcements
    active_announcements = Announcement.query.filter_by(is_active=True).count()
    
    return render_template(
        "admin/dashboard.html",
        announcement_stats={
            'total': total_announcements,
            'active': active_announcements
        }
    )

@app.route("/admin/sit-in-records")
def admin_sit_in_records():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/sit-in-records.html")

@app.route("/admin/sit-in-reports")
def admin_sit_in_reports():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/sit-in-reports.html")

@app.route("/admin/feedback-reports")
def admin_feedback_reports():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/feedback-reports.html")

@app.route("/admin/search-students")
def admin_search_students():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/search-students.html")

@app.route("/admin/sit-in-form")
def admin_sit_in_form():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/sit-in-form.html")

@app.route("/admin/reservation")
def admin_reservation():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/reservation.html")

# Admin announcements routes
@app.route("/admin/announcements")
def admin_announcements():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    announcements = Announcement.get_all_announcements()
    return render_template("admin/announcements.html", announcements=announcements)

@app.route("/admin/announcements/create", methods=["POST"])
def admin_create_announcement():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    title = request.form.get('title')
    content = request.form.get('content')
    priority = int(request.form.get('priority', 0))
    is_active = request.form.get('is_active') == 'on'
    
    if not title or not content:
        flash("Title and content are required")
        return redirect(url_for('admin_announcements'))
    
    new_announcement = Announcement(
        title=title,
        content=content,
        priority=priority,
        is_active=is_active
    )
    
    db.session.add(new_announcement)
    db.session.commit()
    
    flash("Announcement created successfully")
    return redirect(url_for('admin_announcements'))

@app.route("/admin/announcements/edit/<int:id>", methods=["POST"])
def admin_edit_announcement(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    announcement = Announcement.get_announcement_by_id(id)
    if not announcement:
        flash("Announcement not found")
        return redirect(url_for('admin_announcements'))
    
    announcement.title = request.form.get('title')
    announcement.content = request.form.get('content')
    announcement.priority = int(request.form.get('priority', 0))
    announcement.is_active = request.form.get('is_active') == 'on'
    
    db.session.commit()
    
    flash("Announcement updated successfully")
    return redirect(url_for('admin_announcements'))

@app.route("/admin/announcements/delete/<int:id>", methods=["POST"])
def admin_delete_announcement(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    announcement = Announcement.get_announcement_by_id(id)
    if announcement:
        db.session.delete(announcement)
        db.session.commit()
        flash("Announcement deleted successfully")
    else:
        flash("Announcement not found")
    
    return redirect(url_for('admin_announcements'))

@app.route("/admin/announcements/toggle/<int:id>", methods=["POST"])
def admin_toggle_announcement(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    announcement = Announcement.get_announcement_by_id(id)
    if announcement:
        announcement.is_active = not announcement.is_active
        db.session.commit()
        status = "activated" if announcement.is_active else "deactivated"
        flash(f"Announcement {status} successfully")
    else:
        flash("Announcement not found")
    
    return redirect(url_for('admin_announcements'))

@app.route("/admin/start-sit-in", methods=["POST"])
def admin_start_sit_in():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    student_id = request.form.get('student_id')
    computer_number = request.form.get('computer_number')
    purpose = request.form.get('purpose')
    notes = request.form.get('notes')
    
    if not student_id or not computer_number or not purpose:
        flash("Student ID, computer number, and purpose are required")
        return redirect(url_for('admin_sit_in_form'))
    
    user = User.get_user_by_idno(student_id)
    if not user:
        flash("Student not found")
        return redirect(url_for('admin_sit_in_form'))
    
    # Check if the user has available sessions
    if user.student_session <= 0:
        flash("Student has no available sit-in sessions remaining")
        return redirect(url_for('admin_sit_in_form'))
    
    # Create new sit-in session
    new_session = SitInSession(
        user_id=user.id,
        computer_number=computer_number,
        purpose=purpose,
        notes=notes
    )
    
    # Deduct one session from the user's available sessions
    user.deduct_session()
    
    db.session.add(new_session)
    db.session.commit()
    
    flash("Sit-in session started successfully")
    return redirect(url_for('admin_sit_in_form'))

@app.route("/admin/end-sit-in/<int:session_id>", methods=["POST"])
def admin_end_sit_in(session_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    sit_in_session = SitInSession.get_session_by_id(session_id)
    if not sit_in_session:
        flash("Sit-in session not found")
        return redirect(url_for('admin_sit_in_form'))
    
    # End the sit-in session
    sit_in_session.end_session()
    db.session.commit()
    
    flash("Sit-in session ended successfully")
    return redirect(url_for('admin_sit_in_form'))

@app.route("/admin/search-student", methods=["POST"])
def admin_search_student():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    search_term = request.form.get('student_search')
    if not search_term:
        return jsonify({'success': False, 'message': 'Search term is required'})
    
    # Search for students by ID or name
    users = User.query.filter(
        (User.idno.like(f"%{search_term}%")) |
        (User.firstname.like(f"%{search_term}%")) |
        (User.lastname.like(f"%{search_term}%"))
    ).limit(5).all()
    
    if not users:
        return jsonify({'success': False, 'message': 'No students found'})
    
    # Format user data for response
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'idno': user.idno,
            'name': f"{user.firstname} {user.lastname}",
            'course': user.course,
            'year_level': user.yearlevel,
            'email': user.email,
            'remaining_sessions': user.student_session,
            'photo_url': user.photo_url or '/static/src/images/userphotos/defaultphoto.png'
        })
    
    return jsonify({'success': True, 'students': user_data})

if __name__ == "__main__":
    app.run(debug=True)