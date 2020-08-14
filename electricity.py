from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

# Initialize a database object
db = SQLAlchemy()

app = Flask(__name__)

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