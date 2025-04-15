### Installation

#### Flask Framework

`pip install flask`

### Database Related

`pip install sqlalchemy`
`pip install flask-sqlalchemy`
`pip install mysqlclient  # For MySQL database`


### Excel and Data Manipulation
`pip install xlsxwriter`
`pip install pandas`

### PDF Generation (ReportLab)
`pip install reportlab`

### Install All Requirements
#### You can install all dependencies at once by creating a requirements.txt file with these packages and running:

`pip install -r requirements.txt`

#### requirements.txt content
flask
sqlalchemy
flask-sqlalchemy
mysqlclient
xlsxwriter
pandas
reportlab
werkzeug

### Running the Flask Application
`python app.py`

### Database Setup (MySQL)
`mysql -u root -p`
#### Create database
`CREATE DATABASE ccs_sitin_project;`