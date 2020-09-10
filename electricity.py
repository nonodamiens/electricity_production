from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pypyodbc
import urllib
import os

app = Flask(__name__)

# Connection informations for SQL database
# --- On Azure ---
server = os.environ['SERVER']
database = os.environ['DB']
username = os.environ['SUPERADMIN']
password = os.environ['PWD']   
driver= '{ODBC Driver 17 for SQL Server}'

params = urllib.parse.quote_plus \
(r'Driver='+driver+';Server=tcp:'+server+',1433;Database='+database+';Uid='+username+';Pwd='+password+';Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')

# Setting the working env
ENV = 'prod'

if ENV == 'dev':
    app.debug = True
    # --- For heroku / postgresql ---
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DEV_URI']
    # --- For Azure sql db ---
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
else:
    app.debug = False
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect={}'.format(params)

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
@app.route('/', methods=['POST'])
def index():
    if request.method == "POST":
        user = request.form['alias']
        password = request.form['password']
        if db.session.query(Users).filter(Users.alias == user).count() == 0 or\
             db.session.query(Users).filter(Users.password == password).count() == 0:
            return render_template('index.html', error = 'Non autorisé')
        else:
            user_query =  db.session.query(Users).filter(Users.alias == user).first()
            session['username'] = user_query.alias
            session['admin'] = False
            line_labels = labels
            line_values = values
            line_predictions = predictions
            line_max = maximum
            line_min = minimum
            return render_template('index.html', max=17000,\
                 labels=line_labels, values=line_values, predictions=line_predictions,\
                     maximum=line_max, minimum=line_min )
    else:
        return render_template('index.html')

@app.route('/admin')
@app.route('/admin', methods=["POST"])
def admin():
    # Session check
    if 'username' in session:
        # Check admin level rights
        if session['admin']:
            # Check request form
            if request.method == "POST":
                if request.form.get('data_type') == 'user_creation':
                    user = request.form['alias']
                    password = request.form['password']
                    admin = bool(int(request.form['account_type']))
                    new_user = Users(alias=user, password=password, administrator=admin)
                    db.session.add(new_user)
                    db.session.commit()
                    return render_template('admin.html', response = 'New user inserted')
                else:
                    return render_template('admin.html', error = 'An error occured, please retry')
            else:
                return render_template('admin.html')
    elif request.method == "POST":
        if request.form.get('data_type') == 'login':
            user = request.form['alias']
            password = request.form['password']
            if db.session.query(Users).filter(Users.alias == user).count() != 1 or\
                db.session.query(Users).filter(Users.password == password).count() != 1:
                return render_template('admin.html', error = 'Wrong login or password')
            else:
                query =  db.session.query(Users).filter(Users.alias == user).first()
                
                if query.administrator:
                    session['username'] = query.alias
                    session['admin'] = True
                    return render_template('admin.html', administrator=query.alias)
                else:
                    return render_template('admin.html', error = 'You are not authorized')
        else:
            return render_template('admin.html', error = 'An error occured, please retry')
    else:
        return render_template('admin.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        session.pop('admin', None)
        flash("Vous êtes déconnecté")
    return redirect(url_for('index'))

@app.route('/admin/logout')
def adminlogout():
    if 'username' in session:
        session.pop('username', None)
        session.pop('admin', None)
        flash("Vous êtes déconnecté")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.secret_key=os.environ['KEY']
    app.run()