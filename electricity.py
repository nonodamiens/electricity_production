from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import pyodbc
import urllib
import os

app = Flask(__name__)

# Connection informations for SQL database
# --- On Azure ---
server = 'denko.database.windows.net'
database = 'electricity_forecast'
username = 'arnaud'
password = os.environ['PWD']   
driver= '{ODBC Driver 17 for SQL Server}'

params = urllib.parse.quote_plus \
(r'Driver='+driver+';Server=tcp:'+server+',1433;Database='+database+';Uid='+username+';Pwd='+password+';Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')

# Setting the working env
ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    # --- For heroku / postgresql ---
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DEV_URI']
    # --- For Azure sql db ---
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(25))
    password = db.Column(db.String(50))
    administrator = db.Column(db.Boolean)

    def __init__(self, alias, password, administrator):
        self.alias = alias
        self.password = password
        self.administrator = administrator

class Electric_prod_fr(db.Model):
    __tablename__ = 'electricity_production_france'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    sourcetype_id = db.Column(db.Integer)
    production_mw = db.Column(db.Integer)

    def __init__(self, date, sourcetype_id, production_mw):
        self.date = date
        self.sourcetype_id = sourcetype_id
        self.proproduction_mw = production_mw

labels = [
    '2020-01', '2020-02', '2020-03', '2020-04',
    '2020-05', '2020-06', '2020-07', '2020-08',
    '2020-09', '2020-10', '2020-11', '2020-12'
]

values = [
    54742, 50788, 48071, 36952,
    37429, 43043, 49012, 45234,
    'NaN', 'NaN', 'NaN', 'NaN'
]

predictions = [
    'NaN', 'NaN', 'NaN', 'NaN',
    'NaN', 'NaN', 'NaN', 'NaN',
    48230, 50432, 52777, 55320
]

maximum = [
    'NaN', 'NaN', 'NaN', 'NaN',
    'NaN', 'NaN', 'NaN', 'NaN',
    50000, 55000, 60000, 65000
]

minimum = [
    'NaN', 'NaN', 'NaN', 'NaN',
    'NaN', 'NaN', 'NaN', 'NaN',
    45000, 45000, 46000, 47000
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello', methods=["POST"])
def hello():
    if request.method == "POST":
        user = request.form['alias']
        password = request.form['password']
        if db.session.query(Users).filter(Users.alias == user).count() == 0 or\
             db.session.query(Users).filter(Users.password == password).count() == 0:
            return 'Non autorisé'
        else:
            line_labels = labels
            line_values = values
            line_predictions = predictions
            line_max = maximum
            line_min = minimum
            return render_template('hello.html', pseudo=user, max=17000,\
                 labels=line_labels, values=line_values, predictions=line_predictions,\
                     maximum=line_max, minimum=line_min )
    else:
        return render_template('hello.html')

@app.route('/admin')
@app.route('/admin', methods=["POST"])
def admin():
    if request.method == "POST":
        user = request.form['alias']
        password = request.form['password']
        if db.session.query(Users).filter(Users.alias == user).count() != 1 or\
             db.session.query(Users).filter(Users.password == password).count() != 1:
            return 'Wrong login or password'
        else:
            query =  db.session.query(Users).filter(Users.alias == user).first()
            print(query.administrator)
            
            if query.administrator:
                return render_template('admin.html', administrator = query.alias)
            else:
                return 'Not authorized'
        return 'page acces et verif connexion'
    else:
        return render_template('admin.html')

if __name__ == '__main__':
    app.run()