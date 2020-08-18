from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

ENV = 'prod'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DEV_URI']
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

labels = [
    'JAN', 'FEB', 'MAR', 'APR',
    'MAY', 'JUN', 'JUL', 'AUG',
    'SEP', 'OCT', 'NOV', 'DEC'
]

values = [
    967.67, 1190.89, 1079.75, 1349.19,
    2328.91, 2504.28, 2873.83, 4764.87,
    4349.29, 6458.30, 9907, 16297
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
            return render_template('hello.html', pseudo=user, max=17000, labels=line_labels, values=line_values)
    else:
        return render_template('hello.html')

@app.route('/admin/<mdp>/<alias>/<password>')
def admin(mdp, alias, password):
    if alias == '' or password == '' or mdp == '':
        return 'No way !'
    elif mdp == os.environ['MDP']:
        if db.session.query(Users).filter(Users.alias == alias).count() == 0:
            data = Users(alias, password)
            db.session.add(data)
            db.session.commit()
            return 'New user saved'
        return 'User already exist'        
    else:
        return 'Unauthorized'

if __name__ == '__main__':
    app.run()