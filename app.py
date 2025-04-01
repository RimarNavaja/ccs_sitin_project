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
from models.feedback import Feedback
from sqlalchemy import text

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1010@localhost/ccs_sitin_project' 
# username - root password - 1010/@Rimar097851 database - ccs_sitin_project/csssitinproject
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = './static/src/images/userphotos'
db.init_app(app)

def check_database_schema():
    """Check and update database schema if needed"""
    try:
        # Check if lab column exists in sit_in_sessions table
        with db.engine.connect() as conn:
            # Try to select from the lab column - if it exists, this will succeed
            result = conn.execute(text("SHOW COLUMNS FROM sit_in_sessions LIKE 'lab'"))
            lab_exists = result.rowcount > 0
            
            # If lab column doesn't exist, add it
            if not lab_exists:
                conn.execute(text("ALTER TABLE sit_in_sessions ADD COLUMN lab VARCHAR(10) AFTER purpose"))
                print("Added missing 'lab' column to sit_in_sessions table")
                
            # Check if computer_number column exists, and drop it if it does
            result = conn.execute(text("SHOW COLUMNS FROM sit_in_sessions LIKE 'computer_number'"))
            computer_number_exists = result.rowcount > 0
            
            if computer_number_exists:
                conn.execute(text("ALTER TABLE sit_in_sessions DROP COLUMN computer_number"))
                print("Removed deprecated 'computer_number' column from sit_in_sessions table")
                
    except Exception as e:
        print(f"Error checking/updating database schema: {e}")

with app.app_context():
    db.create_all()  # Ensure the tables are created
    check_database_schema()  # Check and update schema if needed

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
    # Get active announcements
    announcements = Announcement.get_active_announcements()
    return render_template("index.html", pagetitle="CCS Sit-in", announcements=announcements)

# Admin routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login() -> None:
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        # In a real implementation, check against admin credentials
        # For now, we'll use placeholder credentials
        if username == "admin" and password == "admin123!":
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

@app.route("/admin/get-sit-in-records", methods=["GET"])
def admin_get_sit_in_records():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    # Get query parameters for filtering and pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    date_filter = request.args.get('date_filter', 'all')
    course_filter = request.args.get('course_filter', 'all')
    
    # Start with a base query for completed sessions
    query = SitInSession.query.filter(SitInSession.status == 'completed')
    
    # Apply date filters
    today = datetime.now().date()
    if date_filter == 'today':
        query = query.filter(db.func.date(SitInSession.start_time) == today)
    elif date_filter == 'this_week':
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        query = query.filter(
            db.func.date(SitInSession.start_time) >= start_of_week,
            db.func.date(SitInSession.start_time) <= end_of_week
        )
    elif date_filter == 'this_month':
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        query = query.filter(
            db.func.date(SitInSession.start_time) >= start_of_month,
            db.func.date(SitInSession.start_time) <= end_of_month
        )
    
    # Apply course filter (joins to the User table)
    if course_filter and course_filter.lower() != 'all':
        if course_filter.lower() == 'other':
            query = query.join(User).filter(~User.course.in_(['BSIT', 'BSCS']))
        else:
            query = query.join(User).filter(User.course == course_filter)
    
    # Get total record count for pagination
    total = query.count()
    
    # Order by start_time (newest first) and apply pagination
    records = query.order_by(SitInSession.start_time.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Format records for response
    formatted_records = []
    for record in records:
        user = User.get_user_by_id(record.user_id)
        
        # Format times
        start_time = record.start_time.strftime('%I:%M %p') if record.start_time else 'N/A'
        end_time = record.end_time.strftime('%I:%M %p') if record.end_time else 'N/A'
        date = record.start_time.strftime('%b %d, %Y') if record.start_time else 'N/A'
        
        formatted_records.append({
            'id': record.id,
            'student_id': user.idno,
            'student_name': f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            'purpose': record.purpose,
            'lab': record.lab,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'course': user.course,
            'year_level': user.yearlevel
        })
    
    return jsonify({
        'success': True,
        'records': formatted_records,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page  # Ceiling division
    })

@app.route("/admin/delete-sit-in-record/<int:record_id>", methods=["POST"])
def admin_delete_sit_in_record(record_id):
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    record = SitInSession.get_session_by_id(record_id)
    if not record:
        return jsonify({'success': False, 'message': 'Record not found'})
    
    # Delete the record
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Record deleted successfully'
    })

@app.route("/admin/sit-in-reports")
def admin_sit_in_reports():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/sit-in-reports.html")

@app.route("/admin/feedback-reports")
def admin_feedback_reports():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Get all feedback with related sit-in session and user information
    feedback_list = db.session.query(
        Feedback,
        SitInSession,
        User
    ).join(
        SitInSession, Feedback.session_id == SitInSession.id
    ).join(
        User, SitInSession.user_id == User.id
    ).order_by(Feedback.created_at.desc()).all()
    
    # Get feedback statistics
    feedback_stats = Feedback.get_feedback_stats()
    
    formatted_feedback = []
    for feedback, sit_in, user in feedback_list:
        formatted_feedback.append({
            'id': feedback.id,
            'student_name': f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            'student_id': user.idno,
            'rating': feedback.rating,
            'comments': feedback.comments,
            'purpose': sit_in.purpose,
            'lab': sit_in.lab,
            'date': sit_in.start_time.strftime('%b %d, %Y') if sit_in.start_time else 'N/A',
            'created_at': feedback.created_at.strftime('%b %d, %Y at %I:%M %p')
        })
    
    return render_template(
        "admin/feedback-reports.html",
        feedback_list=formatted_feedback,
        feedback_stats=feedback_stats
    )

@app.route("/admin/student-list")
def admin_student_list():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/student-list.html")

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
    purpose = request.form.get('purpose')
    lab = request.form.get('lab')
    notes = request.form.get('notes')
    send_notification = 'send_notification' in request.form
    
    if not student_id or not purpose or not lab:
        flash("Student ID, purpose, and lab are required")
        return redirect(url_for('admin_sit_in_form'))
    
    user = User.get_user_by_idno(student_id)
    if not user:
        flash("Student not found")
        return redirect(url_for('admin_sit_in_form'))
    
    # Check if the user has available sessions
    if user.student_session <= 0:
        flash("Student has no available sit-in sessions remaining")
        return redirect(url_for('admin_sit_in_form'))
    
    # Check if the user already has an active session
    if SitInSession.user_has_active_session(user.id):
        flash(f"Student {user.firstname.upper()} {user.lastname.upper()} already has an active sit-in session")
        return redirect(url_for('admin_sit_in_form'))
    
    # Create new sit-in session
    new_session = SitInSession(
        user_id=user.id,
        purpose=purpose,
        lab=lab,
        notes=notes
    )
    
    # Deduct one session from the user's available sessions
    user.deduct_session()
    
    db.session.add(new_session)
    db.session.commit()
    
    # TODO: Implement email notification if send_notification is True
    if send_notification:
        # This would be implemented with an email service
        pass
    
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
        # Process the photo_url
        photo_url = user.photo_url or '/static/src/images/userphotos/defaultphoto.png'
        # Remove leading './' if present
        if photo_url.startswith('./'):
            photo_url = photo_url[2:]
        # Ensure it starts with '/'
        if not photo_url.startswith('/') and not photo_url.startswith('http'):
            photo_url = '/' + photo_url
            
        user_data.append({
            'id': user.id,
            'idno': user.idno,
            'name': f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            'course': user.course,
            'year_level': user.yearlevel,
            'email': user.email,
            'remaining_sessions': user.student_session,
            'photo_url': photo_url
        })
    
    return jsonify({'success': True, 'students': user_data})

@app.route("/admin/get-active-sessions")
def admin_get_active_sessions():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    # Get active sessions
    active_sessions = SitInSession.get_active_sessions()
    
    # Format session data for response
    formatted_sessions = []
    for sit_in in active_sessions:
        user = User.query.get(sit_in.user_id)
        # Ensure photo_url is properly formatted
        photo_url = user.photo_url or '/static/src/images/userphotos/defaultphoto.png'
        # Remove leading './' if present
        if photo_url.startswith('./'):
            photo_url = photo_url[2:]
        # Ensure it starts with '/'
        if not photo_url.startswith('/') and not photo_url.startswith('http'):
            photo_url = '/' + photo_url
            
        formatted_sessions.append({
            'id': sit_in.id,
            'student_id': user.idno,
            'student_name': f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            'photo_url': photo_url,
            'start_time': sit_in.start_time.isoformat(),
            'purpose': sit_in.purpose,
            'lab': sit_in.lab,
            'notes': sit_in.notes,
            'remaining_sessions': user.student_session  # Add the remaining sessions
        })
    
    return jsonify({
        'success': True, 
        'sessions': formatted_sessions
    })

@app.route("/admin/get-students", methods=["GET"])
def admin_get_students():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    course_filter = request.args.get('course', '')
    
    # Base query
    query = User.query
    
    # Apply search filter if provided
    if search:
        query = query.filter(
            (User.idno.like(f"%{search}%")) |
            (User.firstname.like(f"%{search}%")) |
            (User.lastname.like(f"%{search}%"))
        )
    
    # Apply course filter if provided
    if course_filter:
        if course_filter == 'OTHER':
            # Filter for courses that are not BSIT or BSCS
            query = query.filter(~User.course.in_(['BSIT', 'BSCS']))
        else:
            query = query.filter(User.course == course_filter)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Format user data
    user_data = []
    for user in users:
        # Process photo URL
        photo_url = user.photo_url or '/static/src/images/userphotos/defaultphoto.png'
        if photo_url.startswith('./'):
            photo_url = photo_url[2:]
        if not photo_url.startswith('/') and not photo_url.startswith('http'):
            photo_url = '/' + photo_url
            
        user_data.append({
            'id': user.id,
            'idno': user.idno,
            'name': f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            'course': user.course,
            'year_level': user.yearlevel,
            'email': user.email,
            'student_session': user.student_session,
            'photo_url': photo_url
        })
    
    return jsonify({
        'success': True,
        'students': user_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page  # Ceiling division
    })

@app.route("/admin/delete-student", methods=["POST"])
def admin_delete_student():
    try:
        if 'admin' not in session:
            return jsonify({'success': False, 'message': 'Not authorized'})
        
        student_id = request.form.get('student_id')
        
        if not student_id:
            return jsonify({'success': False, 'message': 'Student ID is required'})
        
        user = User.query.filter_by(idno=student_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Check if user has active sit-in sessions
        has_active_session = SitInSession.user_has_active_session(user.id)
        if has_active_session:
            return jsonify({'success': False, 'message': 'Cannot delete student with active sit-in session'})
        
        # First, delete all related sit-in sessions (both active and inactive)
        # This prevents the foreign key constraint error
        SitInSession.query.filter_by(user_id=user.id).delete()
        
        # Then delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Student {student_id} deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting student: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error deleting student: {str(e)}'
        })

@app.route("/sitin-history")
def sitin_history():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['user']).first()
    
    # Get filter parameters
    date_filter = request.args.get('date_filter', 'all')
    lab_filter = request.args.get('lab_filter', '')
    
    # Start with base query for the user's completed sessions
    query = SitInSession.query.filter_by(user_id=user.id).filter(SitInSession.status == 'completed')
    
    # Apply date filters
    today = datetime.now().date()
    if date_filter == 'today':
        query = query.filter(db.func.date(SitInSession.start_time) == today)
    elif date_filter == 'this_week':
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        query = query.filter(
            db.func.date(SitInSession.start_time) >= start_of_week,
            db.func.date(SitInSession.start_time) <= end_of_week
        )
    elif date_filter == 'this_month':
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        query = query.filter(
            db.func.date(SitInSession.start_time) >= start_of_month,
            db.func.date(SitInSession.start_time) <= end_of_month
        )
    
    # Apply lab filter if provided
    if lab_filter:
        query = query.filter(SitInSession.lab == lab_filter)
    
    # Get total record count
    total_records = query.count()
    
    # Order by start_time (newest first) and apply pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Set records per page
    sit_in_records = query.order_by(SitInSession.start_time.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Format records for display
    formatted_records = []
    for record in sit_in_records:
        # Check if feedback exists for this session
        has_feedback = Feedback.query.filter_by(session_id=record.id).first() is not None
        
        formatted_records.append({
            'id': record.id,
            'purpose': record.purpose,
            'lab': record.lab,
            'date': record.start_time.strftime('%b %d, %Y') if record.start_time else 'N/A',
            'start_time': record.start_time.strftime('%I:%M %p') if record.start_time else 'N/A',
            'end_time': record.end_time.strftime('%I:%M %p') if record.end_time else 'N/A',
            'has_feedback': has_feedback
        })
    
    return render_template(
        "sitin-history.html", 
        user=user,
        sit_in_records=formatted_records,
        total_records=total_records,
        page=page,
        per_page=per_page,
        total_pages=(total_records + per_page - 1) // per_page  # Ceiling division
    )

@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    session_id = request.form.get('session_id')
    rating = request.form.get('rating')
    comments = request.form.get('comments', '')
    
    if not session_id or not rating:
        flash("Session ID and rating are required")
        return redirect(url_for('sitin_history'))
    
    # Get the sit-in session
    sit_in_session = SitInSession.get_session_by_id(session_id)
    if not sit_in_session:
        flash("Sit-in session not found")
        return redirect(url_for('sitin_history'))
    
    # Check if the session belongs to the user
    user = User.query.filter_by(username=session['user']).first()
    if sit_in_session.user_id != user.id:
        flash("You can only submit feedback for your own sessions")
        return redirect(url_for('sitin_history'))
    
    # Check if feedback already exists for this session
    existing_feedback = Feedback.query.filter_by(session_id=session_id).first()
    if existing_feedback:
        # Update existing feedback
        existing_feedback.rating = rating
        existing_feedback.comments = comments
        db.session.commit()
        flash("Feedback updated successfully")
    else:
        # Create new feedback
        new_feedback = Feedback(
            session_id=session_id,
            rating=int(rating),
            comments=comments
        )
        db.session.add(new_feedback)
        db.session.commit()
        flash("Feedback submitted successfully")
    
    return redirect(url_for('sitin_history'))

if __name__ == "__main__":
    # app.run(debug=True, host='172.19.131.163', port=5000)
    app.run(debug=True)
