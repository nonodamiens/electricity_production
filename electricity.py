from flask import Flask, render_template, request
from models import db
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = ''
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello', methods=["POST"])
def hello():
    if request.method == "POST":
        user = request.form['alias']
        password = request.form['password']
        if db.session.query(Users).filter(Users.alias == user).count() == 0:
            return 'Non autorisé'
        else:
            return render_template('hello.html', pseudo=user)
    else:
        return render_template('hello.html')

if __name__ == '__main__':
    app.run()