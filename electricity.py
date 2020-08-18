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