from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pyodbc
import urllib
import os
from models import db_update, csv_upload
from werkzeug.utils import secure_filename

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
ENV = 'dev'

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

class Electric_prod_fr_raw_old(db.Model):
    __tablename__ = 'electricity_production_france_raw_old'
    start_date = db.Column(db.DateTime, primary_key=True)
    end_date = db.Column(db.DateTime)
    production_type = db.Column(db.String(50))
    values_json = db.Column(db.Unicode)

    def __init__(self, start_date, end_date, production_type, values_json):
        self.start_date = start_date
        self.end_date = end_date
        self.production_type = production_type
        self.values_json = values_json

class Electric_prod_fr_raw(db.Model):
    __tablename__ = 'electricity_production_france_raw'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    consumption = db.Column(db.Integer)
    rte_forecast = db.Column(db.Integer)
    petrol = db.Column(db.Integer)
    coal = db.Column(db.Integer)
    gas = db.Column(db.Integer)
    nuclear = db.Column(db.Integer)
    wind = db.Column(db.Integer)
    solar = db.Column(db.Integer)
    hydraulic = db.Column(db.Integer)
    bioenergy = db.Column(db.Integer)
    pump = db.Column(db.Integer)
    exchange = db.Column(db.Integer)
    co2 = db.Column(db.Integer)

    def __init__(self, id, date, consumption, rte_forecast, petrol, coal, gas, nuclear, wind, solar, hydraulic, bioenergy, pump, exchange):
        self.id = id
        self.date = date
        self.consumption = consumption
        self.rte_forecast = rte_forecast
        self.petrol = petrol
        self.coal = coal
        self.gas = gas
        self.nuclear = nuclear
        self.wind = wind
        self.solar = solar
        self.hydraulic = hydraulic
        self.bioenergy = bioenergy
        self.pump = pump
        self.exchange = exchange
        self.co2 = co2


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
                # user creation
                if request.form.get('data_type') == 'user_creation':
                    user = request.form['alias']
                    password = request.form['password']
                    admin = bool(int(request.form['account_type']))
                    new_user = Users(alias=user, password=password, administrator=admin)
                    db.session.add(new_user)
                    db.session.commit()
                    return render_template('admin.html', response = 'New user inserted')
                # csv db insert
                elif request.form.get('data_type') == 'csv_file':
                    print('CSV FILE STARTING IF STATEMENTS')
                    if 'file' not in request.files:
                        print('NO FILE')
                        flash('no files uploaded')
                    else:
                        print('HANDLING FILENAME')
                        file = request.files['file']
                        if file.filename =='':
                            print('NO FILENAME')
                            flash('no selected file')
                        elif file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'csv':
                            filename = secure_filename(file.filename)
                            print(filename)
                            print('csv db insert steps')
                            error, response = csv_upload(file)
                            if error:
                                flash(response)
                            else:
                                # Dataframe browsing and database updating
                                nb_updates = 0
                                nb_insert = 0
                                for label, row in response.iterrows():
                                    if db.session.query(Electric_prod_fr_raw).filter(Electric_prod_fr_raw.date == label).count() >= 1:
                                        db.session.query(Electric_prod_fr_raw).filter(Electric_prod_fr_raw.date == label).update(
                                            {
                                                Electric_prod_fr_raw.consumption: row['Consommation'],
                                                Electric_prod_fr_raw.rte_forecast: row['Prévision J'],
                                                Electric_prod_fr_raw.petrol: row['Fioul'],
                                                Electric_prod_fr_raw.coal: row['Charbon'],
                                                Electric_prod_fr_raw.gas: row['Gaz'],
                                                Electric_prod_fr_raw.nuclear: row['Nucléaire'],
                                                Electric_prod_fr_raw.wind: row['Eolien'],
                                                Electric_prod_fr_raw.solar: row['Solaire'],
                                                Electric_prod_fr_raw.hydraulic: row['Hydraulique'],
                                                Electric_prod_fr_raw.bioenergy: row['Bioénergies'],
                                                Electric_prod_fr_raw.pump: row['Pompage'],
                                                Electric_prod_fr_raw.exchange: row['Ech. physiques'],
                                                Electric_prod_fr_raw.co2: row['Taux de Co2']
                                            }
                                        )
                                        db.session.commit()
                                        print('The database row', label, 'has been updated')
                                        nb_updates += 1
                                    else:
                                        print('db insert')
                                        nb_insert += 1
                                print(nb_updates, 'rows of database have been updated')
                                print(nb_insert, 'rows of database have been inserted')
                            return render_template('admin.html')
                # Database update
                elif request.form.get('data_type') == 'update':
                    print('update automatic db')
                    # Call the function
                    response = db_update(sandbox=True)
                    print(response)
                    flash("db update (code to complete)")
                    return render_template('admin.html')
                else:
                    return render_template('admin.html', error = 'An error occured, please retry')
            else:
                return render_template('admin.html')
    # no session login check
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
    if ENV == 'dev':
        app.run(host='0.0.0.0')
    else:
        app.run(host='0.0.0.0', port=80)