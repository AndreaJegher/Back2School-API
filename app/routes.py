from app import app
from flask import request, render_template

@app.route('/')
def index():
    return render_template('index.html', title='B2S - Home')

@app.route('/login')
def login():
    return render_template('login.html', title='B2S - Login')

@app.route('/register')
def register():
    return render_template('register.html', title='B2S - Register')
