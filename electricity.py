from flask import Flask, render_template, request, session, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import pyodbc
import urllib
import os
from models import db_update, csv_upload, get_data, training
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import time
from datetime import datetime, date, timedelta
import json
import pandas as pd
import numpy as np
from statsmodels.tsa.api import ExponentialSmoothing
import statsmodels.api as sm

app = Flask(__name__)

# Connection informations for SQL database
# --- On Azure ---
load_dotenv()

server = os.getenv('SERVER')
database = os.getenv('DB')
username = os.getenv('SUPERADMIN')
password = os.getenv('PASS')   
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
    password = db.Column(db.String(100))
    administrator = db.Column(db.Boolean)

    def __init__(self, alias, password, administrator):
        self.alias = alias
        self.password = password
        self.administrator = administrator

class Electric_prod_fr(db.Model):
    __tablename__ = 'electricity_production_fr'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    sourcetype_id = db.Column(db.Integer)
    production_mw = db.Column(db.Integer)

    def __init__(self, date, sourcetype_id, production_mw):
        self.date = date
        self.sourcetype_id = sourcetype_id
        self.production_mw = production_mw

class Electric_source_type(db.Model):
    __tablename__ = 'electricity_source_type'
    source_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    category_type = db.Column(db.String(25))

    def __init__(self, source_id, name, category_type):
        self.source_id = source_id
        self.name = name
        self.category_type = category_type

class Electric_source_type_category(db.Model):
    __tablename__ = 'electricity_source_type_category'
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))

    def __init__(self, category_id, name):
        self.category_id = category_id
        self.name = name

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

    def __init__(self, date, consumption, rte_forecast, petrol, coal, gas, nuclear, wind, solar, hydraulic, bioenergy, pump, exchange, co2):
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

@app.route('/')
@app.route('/', methods=['POST'])
def index():
    if request.method == "POST":
        user = request.form['alias']
        password = request.form['password']
        user_db = db.session.query(Users).filter(Users.alias == user).first()
        if db.session.query(Users).filter(Users.alias == user).count() == 1 and \
             check_password_hash(user_db.password, password):
            user_query =  db.session.query(Users).filter(Users.alias == user).first()
            session['username'] = user_query.alias
            session['admin'] = False
            # Get the data for graph
            date_filter_start = datetime(datetime.today().year - 1, datetime.today().month, 1)
            date_filter_end = datetime(datetime.today().year, datetime.today().month, 1)
            print(date_filter_start.year, date_filter_start.month)
            print(date_filter_end.year, date_filter_end.month)
            dates = db.session.query(Electric_prod_fr.date).filter(Electric_prod_fr.date >= date_filter_start, Electric_prod_fr.date < date_filter_end).all()
            dates_list = [d[0] for d in dates]
            productions = db.session.query(Electric_prod_fr.production_mw).filter(Electric_prod_fr.date >= date_filter_start, Electric_prod_fr.date < date_filter_end).all()
            productions_list = [int(p[0]) for p in productions]

            labels, values, predictions, maximum, minimum = get_data(dates_list, productions_list)

            return render_template('index.html', max=17000, labels=labels, values=values, predictions=predictions, maximum=maximum, minimum=minimum)
        else:
            flash('Identifiants inconnus - accès refusé')
            return render_template('index.html')
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
                    # check fields
                    if 'account_type' in request.form and 'alias' in request.form and 'password' in request.form:
                        user = request.form['alias']
                        password = generate_password_hash(request.form['password'], method='sha256')
                        admin = bool(int(request.form['account_type']))
                        new_user = Users(alias=user, password=password, administrator=admin)
                        db.session.add(new_user)
                        db.session.commit()
                        return render_template('admin.html', response = 'New user inserted')
                    else:
                        flash('Il manque des informations')
                        return render_template('admin.html')
                # csv db insert
                elif request.form.get('data_type') == 'csv_file':
                    if 'file' not in request.files:
                        flash('no files uploaded')
                        return render_template('admin.html')
                    else:
                        file = request.files['file']
                        if file.filename =='':
                            flash('no selected file')
                            return render_template('admin.html')
                        elif file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'csv':
                            print('csv db insert steps')
                            error, response = csv_upload(file)
                            if error:
                                flash(response)
                                return render_template('admin.html')
                            else:
                                # Dataframe browsing and database updating
                                def inner():
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
                                            if db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label).count() >= 1:
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 1).update( { Electric_prod_fr.production_mw: row['Nucléaire'] } )
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 3).update( { Electric_prod_fr.production_mw: row['Charbon'] } )
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 2).update( { Electric_prod_fr.production_mw: row['Gaz'] } )
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 4).update( { Electric_prod_fr.production_mw: row['Fioul'] } )
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 5).update( { Electric_prod_fr.production_mw: row['Hydraulique'] } )
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 6).update( { Electric_prod_fr.production_mw: row['Eolien'] } )
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 7).update( { Electric_prod_fr.production_mw: row['Solaire'] } )
                                                db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == label, Electric_prod_fr.sourcetype_id == 8).update( { Electric_prod_fr.production_mw: row['Bioénergies'] } )
                                            else:
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 1, production_mw = row['Nucléaire']))
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 2, production_mw = row['Gaz']))
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 3, production_mw = row['Charbon']))
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 4, production_mw = row['Fioul']))
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 5, production_mw = row['Hydraulique']))
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 6, production_mw = row['Eolien']))
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 7, production_mw = row['Solaire']))
                                                db.session.add(Electric_prod_fr(date = label, sourcetype_id = 8, production_mw = row['Bioénergies']))
                                            db.session.commit()
                                            yield 'The database row ' + str(label) + ' has been updated<br/>\n'
                                            nb_updates += 1
                                        else:
                                            new_data = Electric_prod_fr_raw(
                                                    date = label,
                                                    consumption = row['Consommation'],
                                                    rte_forecast = row['Prévision J'],
                                                    petrol = row['Fioul'],
                                                    coal = row['Charbon'],
                                                    gas = row['Gaz'],
                                                    nuclear = row['Nucléaire'],
                                                    wind = row['Eolien'],
                                                    solar = row['Solaire'],
                                                    hydraulic = row['Hydraulique'],
                                                    bioenergy = row['Bioénergies'],
                                                    pump = row['Pompage'],
                                                    exchange = row['Ech. physiques'],
                                                    co2 = row['Taux de Co2']
                                            )
                                            db.session.add(new_data)
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 1, production_mw = row['Nucléaire']))
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 2, production_mw = row['Gaz']))
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 3, production_mw = row['Charbon']))
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 4, production_mw = row['Fioul']))
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 5, production_mw = row['Hydraulique']))
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 6, production_mw = row['Eolien']))
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 7, production_mw = row['Solaire']))
                                            db.session.add(Electric_prod_fr(date = label, sourcetype_id = 8, production_mw = row['Bioénergies']))
                                            db.session.commit()
                                            yield 'The database row ' + str(label) + ' has been inserted<br/>\n'
                                            nb_insert += 1
                                    yield str(nb_updates) + 'rows of database have been updated<br/>\n'
                                    yield str(nb_insert) + 'rows of database have been inserted<br/>\n'
                                    time.sleep(4)
                                    yield '<script>document.location.href="admin"</script>'
                                return Response(inner())
                        return render_template('admin.html')
                # Database update
                elif request.form.get('data_type') == 'update':
                    # Call the function with dates to setup
                    if request.form.get('start_date') != '':
                        start_date = str(date(int(request.form.get('start_date')[:4]), int(request.form.get('start_date')[5:7]), int(request.form.get('start_date')[8:]))) + 'T00:00:00+00:00'
                    else:
                        start_date = None
                    if request.form.get('end_date') != '':
                        end_date = str(date(int(request.form.get('end_date')[:4]), int(request.form.get('end_date')[5:7]), int(request.form.get('end_date')[8:]))) + 'T23:59:59+00:00'
                    else:
                        end_date = None
                    # start_date = start_date - timedelta(days=1)
                    # start_date = str(start_date) + 'T00:00:00+00:00'
                    # end_date = str(end_date) + 'T23:59:59+00:00'
                    print(start_date, end_date)
                    response = db_update(start_date, end_date)
                    # print(response) # check network response
                    response_loaded = json.loads(response)
                    print(response_loaded)
                    df = pd.DataFrame() # Dataframe instantiation
                    # Source_id correspondence
                    source_id = {'BIOMASS': 8, 'OTHER_RENEWABLE': 8, 'FOSSIL_BROWN_COAL_LIGNITE': 3, 'FOSSIL_COAL_DERIVED_GAS': 3, 'FOSSIL_HARD_COAL': 3, 'FOSSIL_GAS': 2,
                                'FOSSIL_OIL': 4, 'FOSSIL_OIL_SHALE': 4, 'GEOTHERMAL': 5, 'HYDRO_RUN_OF_RIVER_AND_POUNDAGE': 5, 'HYDRO_WATER_RESERVOIR': 5, 'MARINE': 5,
                                'NUCLEAR': 1, 'SOLAR': 7, 'WIND_OFFSHORE': 6, 'WIND_ONSHORE': 6, 'HYDRO_PUMPED_STORAGE': 0, 'WASTE': 8, 'TOTAL': 0}
                    
                    for source in response_loaded['actual_generations_per_production_type']:
                        datas = [{'source': source_id[source['production_type']], 'date': x['start_date'][:10], 'prod': x['value']} for x in source['values']]
                        df = df.append(pd.DataFrame(datas), ignore_index=True)

                    # delete unusable rows
                    df = df[df.source != 0]

                    for indexes, datas in df.groupby(['date', 'source']):
                        # check data already in db
                        if db.session.query(Electric_prod_fr.date).filter(Electric_prod_fr.date == indexes[0], Electric_prod_fr.sourcetype_id == int(indexes[1])).count() >= 1:
                            # db update
                            db.session.query(Electric_prod_fr).filter(Electric_prod_fr.date == indexes[0], Electric_prod_fr.sourcetype_id == int(indexes[1])).update(
                                { Electric_prod_fr.production_mw : int(datas.groupby('source', as_index=False).sum()['prod'][0]) }
                            )
                            db.session.commit()
                            print('row ', indexes[0], ' and source ', indexes[1], ' updated')
                        else:
                            # db add
                            new_data = Electric_prod_fr(date = indexes[0], sourcetype_id = int(indexes[1]), production_mw = int(datas.groupby('source', as_index=False).sum()['prod'][0]))
                            db.session.add(new_data)
                            db.session.commit()
                            print('row ', indexes[0], ' and source ', indexes[1], ' added')
                    # updating model
                    data = db.session.query(Electric_prod_fr.date, Electric_prod_fr.production_mw).all()
                    training(data)
                    flash("db updated")
                    return render_template('admin.html')
                else:
                    flash('Il y eu une erreur, merci de réessayer')
                    return render_template('admin.html')
            else:
                return render_template('admin.html')
        else:
            # Wrong session
            if 'username' in session:
                session.pop('username', None)
                session.pop('admin', None)
            return redirect(url_for('admin'))
    # no session login check
    elif request.method == "POST":
        if request.form.get('data_type') == 'login':
            user = request.form['alias']
            password = request.form['password']
            user_db = db.session.query(Users).filter(Users.alias == user).first()
            if db.session.query(Users).filter(Users.alias == user).count() != 1 or\
                check_password_hash(user_db.password, password) != True:
                flash('Identifiants inconnus')
                return render_template('admin.html')
            else:
                query =  db.session.query(Users).filter(Users.alias == user).first()
                if query.administrator:
                    session['username'] = query.alias
                    session['admin'] = True
                    return render_template('admin.html', administrator=query.alias)
                else:
                    flash('Vous n\'êtes pas autorisé à accéder à l\'interface administrateur')
                    return render_template('admin.html')
        else:
            flash('Il y a eu une erreur, merci de réessayer')
            return render_template('admin.html')
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

@app.route('/tests')
def tests():
    # datas
    query = db.session.query(Electric_prod_fr.date, Electric_prod_fr.production_mw).all()
    df = pd.DataFrame([x for x in query], columns = ['date', 'prod'])
    df.date = pd.to_datetime(df.date)
    df = df.set_index('date')
    df = df.groupby(pd.Grouper(freq='M')).sum()
    df = df.set_index(df.index.to_period("M"))
    print(df['prod'].head())

    hw = ExponentialSmoothing(np.asarray(df["prod"]), seasonal_periods=12, trend='mul', seasonal='mul').fit()
    hw_pred = hw.forecast(4)
    print(hw_pred)

    hw.save("hotwinter.pickle")

    return 'page de tests'

if __name__ == '__main__':
    app.secret_key=os.getenv('KEY')
    if ENV == 'dev':
        app.run(host='0.0.0.0')
    else:
        app.run(host='0.0.0.0', port=80)