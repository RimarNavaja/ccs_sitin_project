from flask import (
    Flask, # Core Flask application class
    render_template, # Renders HTML templates
    request,  # Handles HTTP requests
    redirect,  # Redirects to different routes
    url_for,  # Generates URLs for routes
    flash,
    session, # Handles user sessions  
    jsonify,# Converts data to JSON response
    Response, # Added for CSV export
    send_file, # Sends files to client
    g
)
from werkzeug.utils import secure_filename # Secures uploaded filenames
import os  # Operating system operations
from dbhelper import db, User, Announcement, ComputerStatus # Custom database models
from datetime import timedelta, datetime  # Date and time operations
from models.sit_in_session import SitInSession  # Sit-in session model
from models.feedback import Feedback  # Feedback model
from sqlalchemy import text, or_, func, desc, not_ # Added or_ for searching, func and desc for leaderboard query
import csv # Added for CSV export
from io import StringIO # Added for CSV export
from reportlab.lib.enums import TA_CENTER, TA_LEFT # Import TA_CENTER for alignment
from reportlab.lib.colors import HexColor # Import HexColor
import pandas as pd # Data manipulation library
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet,  ParagraphStyle
from reportlab.platypus import Paragraph
import xlsxwriter # Excel file creation

# --- Define Colors based on HTML ---
COLOR_PURPLE_900 = '#4C1D95' # Tailwind purple-900
COLOR_YELLOW_300 = '#fcba03' # Tailwind yellow-300
COLOR_GRAY_100 = '#F3F4F6'   # Tailwind gray-100 (for alternating rows)
COLOR_GRAY_500 = '#6B7280'   # Tailwind gray-500 (for grid lines)
COLOR_WHITE = '#FFFFFF'
COLOR_BLACK = '#000000'

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1010@localhost/ccs_sitin_project'
# username - root password - 1010/@Rimar097851 database - ccs_sitin_project
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
    sitinsession = SitInSession.query.filter_by( status='active').first()
    announcements = Announcement.get_active_announcements()
    coloractive = "bg-green-200 text-green-700"
    colorinactive = "bg-gray-300"
    # Notification: count unseen approved/disapproved reservations
    notif_count = SitInSession.query.filter(
        SitInSession.user_id == user.id,
        SitInSession.status.in_(["approved", "disapproved"]),
        SitInSession.notified == False
    ).count()
    return render_template("dashboard.html", user=user, announcements=announcements, sitinsession=sitinsession, coloractive=coloractive, colorinactive=colorinactive, notif_count=notif_count)

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
        # temporary admin credentials
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
    active_announcements = Announcement.query.filter_by(is_active=True).count()

    # Get total students and active sit-ins
    total_students = User.query.count()
    active_sitins = SitInSession.query.filter_by(status='active').count()

    # Get today's sit-ins (including active and completed today)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    today_sitins_count = SitInSession.query.filter(
        SitInSession.start_time >= today_start,
        SitInSession.start_time < today_end,
        or_(SitInSession.status == 'active', SitInSession.status == 'completed')
    ).count()

    # Get pending reservations count
    pending_reservations_count = SitInSession.query.filter_by(status='pending').count()

    # Get recent activities (limit 3, including pending, approved, active, completed, disapproved)
    recent_activities = []
    activities = SitInSession.query.join(User)\
                                   .order_by(desc(SitInSession.start_time))\
                                   .limit(5)\
                                   .all() # Fetch more to show variety

    for activity in activities:
        user = activity.user # Access user directly via relationship
        recent_activities.append({
            'student_name': f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            'start_time': activity.start_time.strftime('%b %d, %I:%M %p') if activity.start_time else '-',
            'end_time': activity.end_time.strftime('%I:%M %p') if activity.end_time else '-', # Shows processed time for pending
            'session_count': user.student_session, # Current remaining sessions
            'status': activity.status
        })

    return render_template(
        "admin/dashboard.html",
        dashboard_stats={
            'total_announcements': total_announcements,
            'active_announcements': active_announcements,
            'total_students': total_students,
            'active_sitins': active_sitins,
            'today_sitins': today_sitins_count,
            'pending_reservations': pending_reservations_count # Pass pending count
        },
        recent_activities=recent_activities
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

    try:
        record = SitInSession.get_session_by_id(record_id)
        if not record:
            return jsonify({'success': False, 'message': 'Record not found'})

        # First delete associated feedback if it exists
        feedback = Feedback.query.filter_by(session_id=record_id).first()
        if feedback:
            db.session.delete(feedback)
            
        # Then delete the sit-in session record
        db.session.delete(record)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Record deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting record: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error deleting record: {str(e)}'
        })

@app.route("/admin/sit-in-reports")
def admin_sit_in_reports():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template("admin/sit-in-reports.html")



@app.route("/admin/generate-reports", methods=["GET"])
def admin_generate_reports():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Fetch distinct labs and purposes for filter dropdowns
    distinct_labs = db.session.query(SitInSession.lab).distinct().order_by(SitInSession.lab).all()
    distinct_purposes = db.session.query(SitInSession.purpose).distinct().order_by(SitInSession.purpose).all()

    # Extract values from tuples
    labs = [lab[0] for lab in distinct_labs if lab[0]]
    purposes = [purpose[0] for purpose in distinct_purposes if purpose[0]]

    # Initial rendering of the page (no data yet)
    return render_template("admin/generate_reports.html",
                           labs=labs,
                           purposes=purposes,
                           results=[])



@app.route("/admin/fetch-report-data", methods=["GET"])
def admin_fetch_report_data():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'}), 401

    lab_filter = request.args.get('lab', '')
    purpose_filter = request.args.get('purpose', '')

    # Base query joining SitInSession and User
    query = db.session.query(
        SitInSession,
        User
    ).join(
        User, SitInSession.user_id == User.id
    ).filter(SitInSession.status == 'completed') # Assuming you only want completed sessions for reports

    # Apply filters
    if lab_filter:
        query = query.filter(SitInSession.lab == lab_filter)
    if purpose_filter:
        query = query.filter(SitInSession.purpose == purpose_filter)

    # Order results (e.g., by date)
    query = query.order_by(SitInSession.start_time.desc())

    results = query.all()

    # Format data for JSON response
    formatted_results = []
    for sit_in, user in results:
        formatted_results.append({
            'id': sit_in.id,
            'idno': user.idno,
            'student_name': f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            'course': user.course,
            'purpose': sit_in.purpose,
            'lab': sit_in.lab,
            'date': sit_in.start_time.strftime('%Y-%m-%d') if sit_in.start_time else 'N/A',
            'time_in': sit_in.start_time.strftime('%I:%M %p') if sit_in.start_time else 'N/A',
            'time_out': sit_in.end_time.strftime('%I:%M %p') if sit_in.end_time else 'N/A',
        })

    return jsonify({'success': True, 'results': formatted_results})


@app.route("/admin/feedback-reports")
def admin_feedback_reports():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    rating = request.args.get('rating', '')

    # Base query for all feedback with related session and user information
    query = db.session.query(
        Feedback,
        SitInSession,
        User
    ).join(
        SitInSession, Feedback.session_id == SitInSession.id
    ).join(
        User, SitInSession.user_id == User.id
    )

    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_( # Use or_ here
                User.firstname.like(search_term),
                User.lastname.like(search_term),
                Feedback.comments.like(search_term)
            )
        )

    # Apply rating filter if provided
    if rating and rating.isdigit():
        query = query.filter(Feedback.rating == int(rating))

    # Get total count for pagination
    total_records = query.count()

    # Apply pagination
    query = query.order_by(Feedback.created_at.desc())
    paginated_results = query.offset((page - 1) * per_page).limit(per_page).all()

    # Calculate pagination details
    total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None
    start_record = (page - 1) * per_page + 1 if total_records > 0 else 0
    end_record = min(page * per_page, total_records)

    # Format the feedback data
    formatted_feedback = []
    for feedback, sit_in, user in paginated_results:
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

    # Get feedback statistics
    feedback_stats = Feedback.get_feedback_stats()

    return render_template(
        "admin/feedback-reports.html",
        feedback_list=formatted_feedback,
        feedback_stats=feedback_stats,
        page=page,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
        start_record=start_record,
        end_record=end_record,
        total_records=total_records,
        search=search,
        rating=rating
    )

@app.route("/admin/export-feedback-pdf")
def admin_export_feedback_pdf():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Get query parameters
    search = request.args.get('search', '')
    rating = request.args.get('rating', '')

    # Base query for all feedback with related session and user information
    query = db.session.query(
        Feedback,
        SitInSession,
        User
    ).join(
        SitInSession, Feedback.session_id == SitInSession.id
    ).join(
        User, SitInSession.user_id == User.id
    )

    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.firstname.like(search_term),
                User.lastname.like(search_term),
                Feedback.comments.like(search_term)
            )
        )

    # Apply rating filter if provided
    if rating and rating.isdigit():
        query = query.filter(Feedback.rating == int(rating))

    # Get all matching records
    results = query.order_by(Feedback.created_at.desc()).all()

    # --- Prepare Data ---
    headers = ['Student ID', 'Student Name', 'Rating', 'Comments', 'Purpose', 'Lab', 'Date', 'Submission Time']
    data = []
    for feedback, sit_in, user in results:
        data.append([
            user.idno,
            f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            feedback.rating,
            feedback.comments or 'No comments provided',
            sit_in.purpose,
            sit_in.lab,
            sit_in.start_time.strftime('%b %d, %Y') if sit_in.start_time else 'N/A',
            feedback.created_at.strftime('%Y-%m-%d %I:%M %p')
        ])

    # --- Report Header Utility Function ---
    def get_report_header_lines():
        return [
            "University of Cebu - Main Campus",
            "College of Computer Studies",
            "Sit-in Feedback Report",
            f"Feedback Report ({datetime.now().strftime('%B %d, %Y')})"
        ]

    # --- PDF Generation ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()

    # Define Custom Styles
    styles.add(ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='MainTitle', parent=styles['h1'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=14, spaceAfter=2))
    styles.add(ParagraphStyle(name='SubTitle', parent=styles['h2'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12, spaceAfter=2))
    styles.add(ParagraphStyle(name='ReportTitle', parent=styles['h3'], alignment=TA_CENTER, fontName='Helvetica', fontSize=11, spaceAfter=10))

    # Build PDF Header
    logo_ccs = "static/src/images/logos/CCS_LOGO.png"
    logo_uc = "static/src/images/logos/UC_LOGO.png"
    try: img_ccs = Image(logo_ccs, width=50, height=50)
    except Exception: img_ccs = Paragraph("(CCS Logo Missing)", styles['Center'])
    try: img_uc = Image(logo_uc, width=50, height=50)
    except Exception: img_uc = Paragraph("(UC Logo Missing)", styles['Center'])

    header_lines_for_pdf = get_report_header_lines()
    header_data = [
        [img_uc, Paragraph(header_lines_for_pdf[0], styles['MainTitle']), img_ccs],
        ['', Paragraph(header_lines_for_pdf[1], styles['SubTitle']), ''],
        ['', Paragraph(header_lines_for_pdf[2], styles['SubTitle']), ''],
        ['', Paragraph(header_lines_for_pdf[3], styles['ReportTitle']), '']
    ]
    header_table = Table(header_data, colWidths=[80, '70%', 80])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 0), (1, 0)), ('SPAN', (1, 1), (1, 1)),
        ('SPAN', (1, 2), (1, 2)), ('SPAN', (1, 3), (1, 3)),
        ('BOTTOMPADDING', (0, 3), (-1, 3), 12),
    ]))
    elements.append(header_table)

    # Prepare Data Table
    if data:
        table_data = [headers] + data
        col_widths = [60, 120, 40, 180, 80, 40, 70,100]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(COLOR_YELLOW_300)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white), ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'), ('ALIGN', (1, 1), (1, -1), 'LEFT'), # Student Name
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Comments
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),    # Purpose
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5), ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor(COLOR_GRAY_500)),
        ]))
        elements.append(table)
    else:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("No feedback found for the selected filters.", styles['Center']))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'feedback_report_{datetime.now().strftime("%Y%m%d")}.pdf'
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

@app.route('/admin/reward-sit-in/<int:session_id>', methods=['POST'])
def admin_reward_sit_in(session_id):
    # Get the session
    session = SitInSession.query.get_or_404(session_id)
    user = User.query.get(session.student_id)
    
    # Add 1 point
    user.lab_points = (user.lab_points or 0) + 1
    
    # Convert points to session if >= 3 but keep the points
    converted = False
    if user.lab_points >= 3 and user.lab_points % 3 == 0:
        user.student_session += 1
        converted = True
    
    # End the session
    session.end_time = datetime.now()
    session.status = 'completed'
    
    db.session.commit()
    
    flash('Session ended and point awarded successfully!', 'success')
    return redirect(url_for('admin_sit_in_form'))



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

@app.route("/admin/reset-session", methods=["POST"])
def admin_reset_session():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})

    student_id = request.form.get('student_id')
    if not student_id:
        return jsonify({'success': False, 'message': 'Student ID is required'})

    user = User.query.filter_by(idno=student_id).first()
    if not user:
        return jsonify({'success': False, 'message': 'Student not found'})

    try:
        # Find completed sessions for the user
        completed_sessions = SitInSession.query.filter_by(user_id=user.id, status='completed').all()
        session_ids = [s.id for s in completed_sessions]

        # Delete associated feedback first if sessions exist
        if session_ids:
            Feedback.query.filter(Feedback.session_id.in_(session_ids)).delete(synchronize_session=False)

        # Now delete the completed sit-in sessions
        if session_ids:
             SitInSession.query.filter_by(user_id=user.id, status='completed').delete(synchronize_session=False)

        # Reset available session count and lab points
        # Assuming User.reset_session_count does NOT commit internally
        if user.course in ['BSIT', 'BSCS', 'BSIS']:
             user.student_session = 30
        else:
             user.student_session = 15
        user.lab_points = 0 # Reset lab points

        db.session.commit() # Commit all changes (deletions and updates)

        return jsonify({
            'success': True,
            'message': f'Sessions, points, and completed session history (including feedback) reset successfully for student {user.firstname} {user.lastname}'
        })
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        print(f"Error resetting session for {student_id}: {str(e)}") # Add logging
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

@app.route("/admin/reset-all-sessions", methods=["POST"])
def admin_reset_all_sessions():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})

    try:
        users = User.query.all()
        for user in users:
            # Find completed sessions for the current user
            completed_sessions = SitInSession.query.filter_by(user_id=user.id, status='completed').all()
            session_ids = [s.id for s in completed_sessions]

            # Delete associated feedback first if sessions exist
            if session_ids:
                Feedback.query.filter(Feedback.session_id.in_(session_ids)).delete(synchronize_session=False)

            # Now delete the completed sit-in sessions
            if session_ids:
                SitInSession.query.filter_by(user_id=user.id, status='completed').delete(synchronize_session=False)

            # Reset available session count and lab points for each user
            # Assuming User.reset_session_count does NOT commit internally
            if user.course in ['BSIT', 'BSCS', 'BSIS']:
                 user.student_session = 30
            else:
                 user.student_session = 15
            user.lab_points = 0 # Reset lab points for each user

        db.session.commit() # Commit all changes after the loop

        return jsonify({
            'success': True,
            'message': 'All student sessions, points, and completed session history (including feedback) have been reset successfully'
        })
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        print(f"Error resetting all sessions: {str(e)}") # Add logging
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

@app.route("/admin/export/<format>")
def admin_export_report(format):
    # --- Authentication Check ---
    if 'admin' not in session:
        flash("Not authorized to export reports.")
        return jsonify({'success': False, 'message': 'Not authorized'}), 401

    # --- Get Filters from Request Arguments ---
    lab_filter = request.args.get('lab', '')
    purpose_filter = request.args.get('purpose', '')

    # --- Database Query ---
    try:
        query = db.session.query(
            SitInSession,
            User
        ).join(
            User, SitInSession.user_id == User.id
        ).filter(SitInSession.status == 'completed')

        if lab_filter:
            query = query.filter(SitInSession.lab == lab_filter)
        if purpose_filter:
            query = query.filter(SitInSession.purpose == purpose_filter)

        query = query.order_by(SitInSession.start_time.desc())
        results = query.all()

    except Exception as e:
        print(f"Error fetching report data for export: {e}")
        flash(f"Error generating report data: {e}")
        return redirect(url_for('admin_generate_reports'))

    # --- Prepare Data ---
    data = []
    headers = ['Sit-in #', 'ID Number', 'Student Name', 'Course', 'Purpose',
               'Lab', 'Date', 'Time In', 'Time Out']

    # Check results (results will be an empty list if none found, not None)
    # No need for 'if results is None:' check here

    for sit_in, user in results:
        data.append([
            sit_in.id,
            user.idno,
            f"{user.firstname.capitalize()} {user.lastname.capitalize()}",
            user.course,
            sit_in.purpose,
            sit_in.lab,
            sit_in.start_time.strftime('%Y-%m-%d') if sit_in.start_time else 'N/A',
            sit_in.start_time.strftime('%I:%M %p') if sit_in.start_time else 'N/A',
            sit_in.end_time.strftime('%I:%M %p') if sit_in.end_time else 'N/A'
        ])

    # --- Report Header Utility Function ---
    def get_report_header_lines():
        return [
            "University of Cebu - Main Campus",
            "College of Computer Studies",
            "Computer Laboratory Sit-in Monitoring System",
            f"Sit-in Report ({datetime.now().strftime('%B %d, %Y')})"
        ]

    # --- EXPORT FORMAT LOGIC ---

    if format.lower() == 'csv':
        output = StringIO()
        writer = csv.writer(output)

        # Write report header
        for header_line in get_report_header_lines():
            writer.writerow([header_line])
        writer.writerow([])  # Empty row for spacing

        writer.writerow(headers)
        if data:
            writer.writerows(data)
        else:
            writer.writerow(["No data found for the selected filters."]) # Indicate no data

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=sit_in_report_{datetime.now().strftime("%Y%m%d")}.csv',
                'Cache-Control': 'no-cache'
            }
        )

    elif format.lower() == 'excel':
        output = BytesIO()
        # Use 'in_memory' option which is generally recommended with BytesIO
        workbook = xlsxwriter.Workbook(output, {'in_memory': True, 'strings_to_numbers': True})
        worksheet = workbook.add_worksheet('Sit-in Report')

        # --- Define Formats ---
        # Using COLOR_PURPLE_900 for main header background again to match PDF/original request
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'font_name': 'Arial', 'valign': 'vcenter'
        })
        # Reverting header format color to purple
        header_format = workbook.add_format({
            'bold': True, 'bg_color': COLOR_PURPLE_900, 'font_color': COLOR_WHITE,
            'border': 1, 'border_color': COLOR_GRAY_500, 'align': 'center',
            'valign': 'vcenter', 'font_name': 'Arial', 'font_size': 11, 'text_wrap': True,
        })
        data_format = workbook.add_format({
            'border': 1, 'border_color': COLOR_GRAY_500, 'align': 'left',
            'valign': 'vcenter', 'font_name': 'Arial', 'font_size': 10,
        })
        data_format_center = workbook.add_format({
            'border': 1, 'border_color': COLOR_GRAY_500, 'align': 'center',
            'valign': 'vcenter', 'font_name': 'Arial', 'font_size': 10,
        })

        # Define which columns should be center-aligned
        center_aligned_cols = [0, 1, 5, 6, 7, 8] # Sit-in #, ID, Lab, Date, Time In, Time Out (Adjusted)

        # --- Write Report Header ---
        current_row = 0
        for header_line in get_report_header_lines():
            worksheet.merge_range(current_row, 0, current_row, len(headers)-1, header_line, title_format)
            worksheet.set_row(current_row, 18) # Set row height for titles
            current_row += 1
        current_row += 1  # Add empty row for spacing

        # --- Write Data Headers ---
        worksheet.set_row(current_row, 20) # Set header row height
        for col, header in enumerate(headers):
            worksheet.write(current_row, col, header, header_format)
        data_start_row = current_row + 1 # Where actual data begins

        # --- Write Data ---
        if data:
            for row_idx, row_data in enumerate(data):
                # Calculate the actual worksheet row index
                worksheet_row = data_start_row + row_idx
                for col_idx, value in enumerate(row_data):
                    chosen_format = data_format_center if col_idx in center_aligned_cols else data_format
                    worksheet.write(worksheet_row, col_idx, value, chosen_format)
        else: # Add a message if no data
             worksheet.merge_range(data_start_row, 0, data_start_row, len(headers)-1,
                                   'No data found for the selected filters.', data_format_center)

        # --- Adjust Column Widths --- *RE-ADDED*
        worksheet.set_column('A:A', 10)  # Sit-in #
        worksheet.set_column('B:B', 15)  # ID Number
        worksheet.set_column('C:C', 25)  # Student Name
        worksheet.set_column('D:D', 15)  # Course
        worksheet.set_column('E:E', 20)  # Purpose
        worksheet.set_column('F:F', 10)  # Lab
        worksheet.set_column('G:G', 12)  # Date
        worksheet.set_column('H:I', 12)  # Time In, Time Out

        # --- Finalize and Send --- *FIXED*
        workbook.close()  # Essential: Finalizes the workbook structure
        output.seek(0)    # Essential: Rewinds the buffer to the beginning

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'sit_in_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )

    elif format.lower() == 'pdf':
        # --- PDF Generation (Keep as is, but ensure header color matches Excel if desired) ---
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=landscape(letter),
            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
        )
        elements = []
        styles = getSampleStyleSheet()

        # Define Custom Styles
        styles.add(ParagraphStyle(name='Center', parent=styles['Normal'], alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='MainTitle', parent=styles['h1'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=14, spaceAfter=2))
        styles.add(ParagraphStyle(name='SubTitle', parent=styles['h2'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=12, spaceAfter=2))
        styles.add(ParagraphStyle(name='ReportTitle', parent=styles['h3'], alignment=TA_CENTER, fontName='Helvetica', fontSize=11, spaceAfter=10))

        # Build PDF Header
        logo_ccs = "static/src/images/logos/CCS_LOGO.png"
        logo_uc = "static/src/images/logos/UC_LOGO.png"
        try: img_ccs = Image(logo_ccs, width=50, height=50)
        except Exception: img_ccs = Paragraph("(CCS Logo Missing)", styles['Center'])
        try: img_uc = Image(logo_uc, width=50, height=50)
        except Exception: img_uc = Paragraph("(UC Logo Missing)", styles['Center'])

        # Use the same header lines function
        header_lines_for_pdf = get_report_header_lines()
        header_data = [
            [img_uc, Paragraph(header_lines_for_pdf[0], styles['MainTitle']), img_ccs],
            ['', Paragraph(header_lines_for_pdf[1], styles['SubTitle']), ''],
            ['', Paragraph(header_lines_for_pdf[2], styles['SubTitle']), ''],
            ['', Paragraph(header_lines_for_pdf[3], styles['ReportTitle']), '']
        ]
        header_table = Table(header_data, colWidths=[80, '70%', 80])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (1, 0), (1, 0)), ('SPAN', (1, 1), (1, 1)),
            ('SPAN', (1, 2), (1, 2)), ('SPAN', (1, 3), (1, 3)),
            ('BOTTOMPADDING', (0, 3), (-1, 3), 12),
        ]))
        elements.append(header_table)

        # Prepare Data Table
        if data:
            table_data = [headers] + data
            col_widths = [50, 80, 140, 80, 110, 50, 70, 70, 70]
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                 
                ('BACKGROUND', (0, 0), (-1, 0), HexColor(COLOR_YELLOW_300)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), # White text on purple
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white), ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'), ('ALIGN', (2, 1), (2, -1), 'LEFT'), # Student Name
                ('ALIGN', (4, 1), (4, -1), 'LEFT'),    # Purpose
                ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5), ('TOPPADDING', (0, 1), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor(COLOR_GRAY_500)),
            ]))
            elements.append(table)
        else:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("No data found for the selected filters.", styles['Center']))

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'sit_in_report_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

    # --- Fallback for Invalid Format ---
    return jsonify({'success': False, 'message': 'Invalid export format requested'}), 400



@app.route("/admin/leaderboard")
def admin_leaderboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Query to get leaderboard data (top 5 students by session count and points)
    leaderboard_data = db.session.query(
        User.idno,
        User.firstname,
        User.lastname,
        User.course,
        func.count(SitInSession.id).label('session_count'),
        User.lab_points
    ).join(SitInSession, User.id == SitInSession.user_id)\
     .filter(SitInSession.status == 'completed')\
     .group_by(User.id)\
     .order_by(desc('session_count'), desc(User.lab_points))\
     .limit(5)\
     .all()

    # Format leaderboard
    formatted_leaderboard = []
    for rank, student in enumerate(leaderboard_data, 1):
        formatted_leaderboard.append({
            'rank': rank,
            'idno': student.idno,
            'name': f"{student.firstname.capitalize()} {student.lastname.capitalize()}",
            'course': student.course,
            'session_count': student.session_count,
            'total_points': student.lab_points or 0
        })

    return render_template("admin/leaderboard.html", leaderboard=formatted_leaderboard)

# Student module - reservation
@app.route("/reservation", methods=["GET", "POST"])
def reservation():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    if request.method == "POST":
        purpose = request.form.get("purpose")
        lab = request.form.get("lab")
        time_in = request.form.get("time_in")
        date = request.form.get("date")
        pc_id = request.form.get("pc_id")

        # --- Validation ---
        if not all([purpose, lab, time_in, date, pc_id]):
            flash("All fields are required.", "error")
            return render_template("reservation.html", user=user)

        try:
            # Combine date and time, check if it's in the past
            requested_datetime_str = f"{date} {time_in}"
            requested_datetime = datetime.strptime(requested_datetime_str, "%Y-%m-%d %H:%M")
            # Allow reservations for the current time or future
            if requested_datetime < datetime.now() - timedelta(minutes=1): # Allow a small buffer
                 flash("Cannot reserve a time in the past.", "error")
                 return render_template("reservation.html", user=user, form_data=request.form)
        except ValueError:
             flash("Invalid date or time format.", "error")
             return render_template("reservation.html", user=user, form_data=request.form)


        if user.student_session <= 0:
            flash("No remaining sit-in sessions.", "error")
            return render_template("reservation.html", user=user, form_data=request.form)

        # Check if user already has an active or pending session
        existing_session = SitInSession.query.filter(
            SitInSession.user_id == user.id,
            or_(SitInSession.status == 'active', SitInSession.status == 'pending')
        ).first()
        if existing_session:
            flash(f"You already have an {existing_session.status} sit-in session or reservation.", "error")
            return render_template("reservation.html", user=user, form_data=request.form)

        # --- Create Reservation ---
        new_session = SitInSession(
            user_id=user.id,
            purpose=purpose,
            lab=lab,
            start_time=requested_datetime, # Store the requested start time
            status="pending" # Initial status is pending approval
        )
        db.session.add(new_session)
        db.session.commit()
        flash("Reservation submitted successfully! Please wait for admin approval.", "success")
        return redirect(url_for('dashboard'))

    # GET request
    return render_template("reservation.html", user=user)

@app.route("/admin/computer-control")
def admin_computer_control():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Fetch computer statuses grouped by lab
    labs_data = ComputerStatus.get_computers_by_lab()
    lab_names = sorted(labs_data.keys()) # Get sorted list of lab names for the filter

    return render_template("admin/computer_control.html", labs_data=labs_data, lab_names=lab_names)

@app.route("/admin/update-computer-status", methods=["POST"])
def admin_update_computer_status():
    if 'admin' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400

    computer_ids = data.get('computer_ids')
    new_status = data.get('status')

    if not computer_ids or not new_status:
        return jsonify({'success': False, 'message': 'Missing computer IDs or status'}), 400

    valid_statuses = ['available', 'used', 'maintenance']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status provided'}), 400

    try:
        # Convert IDs to integers
        computer_ids_int = [int(id) for id in computer_ids]
        updated_count = ComputerStatus.update_status_bulk(computer_ids_int, new_status)
        return jsonify({
            'success': True,
            'message': f'{updated_count} computer(s) updated to {new_status}.'
        })
    except ValueError as ve:
         # Handle case where IDs are not integers
         return jsonify({'success': False, 'message': f'Invalid computer ID format: {ve}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error updating computer status: {e}") # Log the error server-side
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

@app.route("/admin/reservation")
def admin_reservation():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Fetch pending reservations with user data eagerly loaded
    pending_reservations = SitInSession.query.options(db.joinedload(SitInSession.user))\
                                             .filter(SitInSession.status == 'pending')\
                                             .order_by(SitInSession.start_time.asc())\
                                             .all()

    # Fetch processed reservations (approved or disapproved) with user data
    processed_reservations = SitInSession.query.options(db.joinedload(SitInSession.user))\
                                               .filter(or_(SitInSession.status == 'approved', SitInSession.status == 'disapproved'))\
                                               .order_by(SitInSession.end_time.desc())\
                                               .limit(50)\
                                               .all() # Limit logs for performance

    return render_template("admin/admin_reservation.html",
                           pending_reservations=pending_reservations,
                           processed_reservations=processed_reservations)

@app.route("/admin/reservation/approve/<int:session_id>", methods=["POST"])
def admin_approve_reservation(session_id):
    if 'admin' not in session:
        flash("Unauthorized access.", "error")
        return redirect(url_for('admin_login'))

    reservation = SitInSession.query.get(session_id)
    if not reservation:
        flash("Reservation not found.", "error")
        return redirect(url_for('admin_reservation'))

    if reservation.status != 'pending':
        flash("Reservation is not pending.", "error")
        return redirect(url_for('admin_reservation'))   

    user = User.query.get(reservation.user_id)
    if not user:
        flash("Associated user not found.", "error")
        # Clean up orphan reservation?
        reservation.status = 'disapproved' # Mark as disapproved if user is gone
        reservation.end_time = datetime.now()
        db.session.commit()
        return redirect(url_for('admin_reservation'))

    # Check if user has sessions left before approving
    if user.student_session <= 0:
        flash(f"Cannot approve: Student {user.firstname.capitalize()} {user.lastname.capitalize()} has no remaining sessions.", "error")
        reservation.status = 'disapproved'
        reservation.end_time = datetime.now()
        db.session.commit()
        return redirect(url_for('admin_reservation'))

    # Check if user already has another active/approved session
    # Exclude the current reservation being approved
    existing_active_session = SitInSession.query.filter(
        SitInSession.user_id == user.id,
        SitInSession.id != reservation.id, # Exclude self
        or_(SitInSession.status == 'active', SitInSession.status == 'approved')
    ).first()

    if existing_active_session:
        flash(f"Student {user.firstname.capitalize()} {user.lastname.capitalize()} already has another active or approved session.", "error")
        return redirect(url_for('admin_reservation'))

    # --- Approve the reservation ---
    reservation.status = 'approved' # Status indicates admin approved it
    reservation.end_time = datetime.now() # Use end_time to mark processing time
    reservation.notified = False  # <--- Add this line
    # Session count is deducted ONLY when the admin manually starts the session via the Sit-in Form
    db.session.commit()
    flash(f"Reservation for {user.firstname.capitalize()} {user.lastname.capitalize()} approved. Admin must start the session manually via the Sit-in form.", "success")

    return redirect(url_for('admin_reservation'))


@app.route("/admin/reservation/disapprove/<int:session_id>", methods=["POST"])
def admin_disapprove_reservation(session_id):
    if 'admin' not in session:
        flash("Unauthorized access.", "error")
        return redirect(url_for('admin_login'))

    reservation = SitInSession.query.get(session_id)
    if not reservation:
        flash("Reservation not found.", "error")
        return redirect(url_for('admin_reservation'))

    if reservation.status != 'pending':
        flash("Reservation is not pending.", "error")
        return redirect(url_for('admin_reservation'))

    # --- Disapprove the reservation ---
    reservation.status = 'disapproved'
    reservation.end_time = datetime.now() # Use end_time to mark processing time
    reservation.notified = False  # <--- Add this line
    db.session.commit()

    user = User.query.get(reservation.user_id)
    user_name = f"{user.firstname.capitalize()} {user.lastname.capitalize()}" if user else "Unknown User"
    flash(f"Reservation for {user_name} disapproved.", "success")

    return redirect(url_for('admin_reservation'))

@app.route("/api/available-pcs/<lab_name>")
def api_available_pcs(lab_name):
    # Return available PCs for the given lab as JSON
    pcs = ComputerStatus.query.filter_by(lab_name=lab_name, status='available').order_by(ComputerStatus.pc_number).all()
    pc_list = [{"id": pc.id, "pc_number": pc.pc_number} for pc in pcs]
    return jsonify({"pcs": pc_list})

@app.route("/api/reservation-notifications")
def api_reservation_notifications():
    if 'user' not in session:
        return jsonify({"count": 0, "notifications": []})
    user = User.query.filter_by(username=session['user']).first()
    notifs = SitInSession.query.filter(
        SitInSession.user_id == user.id,
        SitInSession.status.in_(["approved", "disapproved"]),
        SitInSession.notified == False
    ).order_by(SitInSession.end_time.desc()).all()
    notif_list = [
        {
            "id": s.id,
            "status": s.status,
            "lab": s.lab,
            "purpose": s.purpose,
            "date": s.start_time.strftime("%b %d, %Y") if s.start_time else "",
            "time": s.start_time.strftime("%I:%M %p") if s.start_time else ""
        }
        for s in notifs
    ]
    return jsonify({"count": len(notif_list), "notifications": notif_list})

@app.route("/api/mark-reservation-notif-read", methods=["POST"])
def api_mark_reservation_notif_read():
    if 'user' not in session:
        return jsonify({"success": False})
    user = User.query.filter_by(username=session['user']).first()
    # Mark all as notified
    SitInSession.query.filter(
        SitInSession.user_id == user.id,
        SitInSession.status.in_(["approved", "disapproved"]),
        SitInSession.notified == False
    ).update({"notified": True})
    db.session.commit()
    return jsonify({"success": True})

if __name__ == "__main__":
    # app.run(debug=True, host='172.19.131.163', port=5000)
    app.run(debug=True)