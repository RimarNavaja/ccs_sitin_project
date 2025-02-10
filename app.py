from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from dbhelper import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1010@localhost/ccs_sitin_project' 
# username - root password - 1010/@Rimar097851 database - ccs_sitin_project/csssitinproject
app.secret_key = 'supersecretkey'
db.init_app(app)

with app.app_context():
    db.create_all()  # Ensure the tables are created

@app.route("/login",  methods=["GET", "POST"])
def login() -> None:
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if User.verify_credentials(username, password):
            flash("Successfully logged in") # temporary message
            return redirect(url_for('dashboard')) # redirect to dashboard
        else:
            flash("Invalid username or password")
            return redirect(url_for('login'))
    return render_template("login.html")

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
            course = request.form['course']
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
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)