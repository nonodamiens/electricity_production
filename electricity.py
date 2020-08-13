from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello', methods=["POST"])
def hello():
    if request.method == "POST":
        return 'Bonjour vous avez mis comme pseudo {} et mdp {}'.format(request.form['pseudo'], request.form['pass'])
    else:
        return 'This is the hello page'