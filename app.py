from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    url_for
)
from werkzeug.utils import secure_filename
import os
from dbhelper import db, User

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
            if User.query.filter_by(username=username).first():
                flash("Username already exists")
                return render_template("register.html", form=request.form.to_dict())

            new_user = User(
                idno=idno,
                lastname=lastname,
                firstname=firstname,
                midname=midname,
                course=course,
                yearlevel=yearlevel,
                email=email,
                username=username,
                password=password
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
    return render_template("dashboard.html", user=user)

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
            user.password = request.form['password']
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

if __name__ == "__main__":
    app.run(debug=True)