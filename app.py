from flask import (
    Flask,
    render_template
)

app = Flask(__name__)

@app.route("/login",  methods=["GET", "POST"])
def login() -> None:
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register() -> None:
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)