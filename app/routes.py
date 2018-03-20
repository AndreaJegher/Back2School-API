from app import app
from flask import request, render_template, make_response
import hashlib, uuid
import os
from functools import wraps
from services.dbservice import load_user, load_session, store_session

def auth_check(fun):
    @wraps(fun)
    def wrapper():

        try:
            sessionid = request.cookies['sessionid']
        except:
            return render_template('login.html', title='B2S - Login', message='Invalid session!')
        session   = load_session(sessionid)

        if contex is not None and session['sessionid'] == sessionid:
            return fun()
        return render_template('login.html', title='B2S - Login', message='Invalid session!')
    return wrapper

@app.route('/')
def index():
    return render_template('index.html', title='B2S - Home')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html', title='B2S - Login')

@app.route('/login', methods=['POST'])
def authenticate():
    username = request.form["username"]
    password = request.form["password"]

    user = load_user(username)

    if user is not None:
        pwdhash = user['pwdhash']
        salt    = user['pwdsalt']
        hashed_password = hashlib.sha512(password + salt).hexdigest()

        if hashed_password == pwdhash:
            sessionid = os.urandom(24)
            store_session(username, sessionid)
            response = make_response(render_template('home.html', title='B2S - home', username=username))
            response.set_cookies['sessionid'] = sessionid
            return response

    return render_template('login.html', title='B2S - Login', message='Invalid username or password!')

@app.route('/register', methods=['GET'])
@auth_check
def register():
    return render_template('register.html', title='B2S - Register')

@app.route('/register', methods=['POST'])
@auth_check
def add_user():
    return render_template('register.html', title='B2S - Register', message=message)

@app.route('/home', methods=['GET'])
@auth_check
def home():
    return render_template('home.html', title='B2S - home', user=user)
