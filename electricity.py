from flask import Flask, render_template, request
from models import db

app = Flask(__name__)

POSTGRES = {
    'user': 'postgres',
    'pw': 'password',
    'db': 'my_database',
    'host': 'localhost',
    'port': '5432',
}

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:\
%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello', methods=["POST"])
def hello():
    if request.method == "POST":
        return render_template('hello.html', pseudo=request.form['pseudo'])
    else:
        return render_template('hello.html')

# debug mode (don't need to restart server at every modification)
app.config['DEBUG'] = True

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')