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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1010@localhost/ccssitinproject' 
# username - root password - 1010
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
def register() -> None:
    if request.method == "POST":
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

            if password != confirm_password:
                flash("Passwords do not match")
                return redirect(url_for('register'))

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
            return redirect(url_for('login'))
        except KeyError as e:
            flash(f"Missing form field: {e}")
            return redirect(url_for('register'))
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)