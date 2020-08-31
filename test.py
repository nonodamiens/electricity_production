import pyodbc
# from sqlalchemy import create_engine
import urllib
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os

params = urllib.parse.quote_plus \
(r'Driver={ODBC Driver 17 for SQL Server};Server=tcp:denko.database.windows.net,1433;Database=electricity_forecast;Uid=arnaud;Pwd='+os.environ['PWD']+';Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
# conn_str = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
# engine_azure = create_engine(conn_str,echo=True)

app = Flask(__name__)

ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    # app.config['SECRET_KEY'] = 'supersecret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
    # app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
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

    def __init__(self, alias, password):
        self.alias = alias
        self.password = password

for u in db.session.query(Users).all() :
    print(u.id, u.alias, u.password)