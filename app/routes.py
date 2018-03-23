from app import app
from flask import request, render_template, make_response, redirect, session
import hashlib, uuid
import os
import binascii
from functools import wraps
from services.dbservice import load_user, load_session, store_session

def auth_check(fun):
    @wraps(fun)
    def wrapper():
        try:
            # sessionid = request.cookies['sessionid']
            sessionid = session['sessionid']
        except:
            return redirect('/login', 302)

        stored_session = load_session(sessionid)
        username = stored_session['username']

        if stored_session is not None and stored_session['sessionid'] == sessionid:
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
        hashed_password = hashlib.sha256(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()

        if hashed_password == pwdhash:
            sessionid = str(binascii.hexlify(os.urandom(24)).decode())
            store_session(username, sessionid)
            response = make_response(redirect('home', 302))
            # response.set_cookie('sessionid', sessionid)
            session['sessionid'] = sessionid
            return response

    return render_template('login.html', title='B2S - Login', message='Invalid username or password!')

@app.route('/home', methods=['GET'])
@auth_check
def home():
    # sessionid = request.cookies['sessionid']
    sessionid = session['sessionid']
    stored_session = load_session(sessionid)
    username = stored_session['username']
    return render_template('home.html', title='B2S - home', username=username)

#All
@app.route('/profile', methods=['GET'])
@auth_check
def get_profile():
    stored_session = load_session(session['sessionid'])
    user = load_user(stored_session['username'])
    return render_template('profile.html', profile=user['profile'])

@app.route('/profile/edit', methods=['GET'])
@auth_check
def get_profile_edit():
    stored_session = load_session(session['sessionid'])
    user = load_user(stored_session['username'])
    return render_template('profile_edit.html', profile=user['profile'], is_admin=True)

@app.route('/profile/edit', methods=['POST'])
@auth_check
def post_profile_edit():
    stored_session = load_session(session['sessionid'])
    user = load_user(stored_session['username'])

    for param in request.form:
        print (param, request.form[param])

    return redirect('/profile', 302)

@app.route('/appointments', methods=['GET'])
@auth_check
def get_appointments():
    return render_template('appointments.html')

@app.route('/appointment', methods=['POST'])
@auth_check
def post_appointment():
    return render_template('appointment.html')

@app.route('/appointment/<id>', methods=['GET'])
@auth_check
def get_appointment(id):
    return render_template('appointment.html')

@app.route('/appointment/<id>', methods=['PUT'])
@auth_check
def put_appointment(id):
    return render_template('appointment.html')

@app.route('/appointment/<id>', methods=['DELETE'])
@auth_check
def delete_appointment(id):
    return render_template('appointment.html')

@app.route('/notifications', methods=['GET'])
@auth_check
def get_notifications():
    return render_template('notifications.html')

@app.route('/notification/<id>', methods=['GET'])
@auth_check
def get_notification(id):
    return render_template('notification.html')

#Parents
@app.route('/children', methods=['GET'])
@auth_check
def get_children():
    return render_template('children.html')

@app.route('/child/<id>/profile', methods=['GET'])
@auth_check
def get_child_profile(id):
    return render_template('child.html')

@app.route('/child/<id>/profile', methods=['PUT'])
@auth_check
def put_child_profile(id):
    return render_template('child.html')

@app.route('/child/<id>/grades', methods=['GET'])
@auth_check
def get_child_grades(id):
    return render_template('child.html')

@app.route('/child/<id>/classes', methods=['GET'])
@auth_check
def get_child_classes(id):
    return render_template('child.html')

@app.route('/payments/all', methods=['GET'])
@auth_check
def get_payments_all():
    return render_template('payments.html')

@app.route('/payments/history', methods=['GET'])
@auth_check
def get_payments_history():
    return render_template('payments.html')

@app.route('/payments/due', methods=['GET'])
@auth_check
def get_payments_due():
    return render_template('payments.html')

@app.route('/payment/<id>', methods=['GET'])
@auth_check
def get_payment(id):
    return render_template('payment.html')

@app.route('/payment/<id>', methods=['POST'])
@auth_check
def post_payment(id):
    return render_template('payment.html')

#Teachers
@app.route('/classes', methods=['GET'])
@auth_check
def get_classes():
    return render_template('classes.html')

@app.route('/class/<id>', methods=['GET'])
@auth_check
def get_class(id):
    return render_template('class.html')

@app.route('/class/<id>/grades', methods=['GET'])
@auth_check
def get_class_grades(id):
    return render_template('class.html')

@app.route('/class/<id>/grade', methods=['POST'])
@auth_check
def post_class_grade(id):
    return render_template('class.html')

@app.route('/class/<class_id>/grade/<grade_id>', methods=['PUT'])
@auth_check
def put_class_grade(class_id, grade_id):
    return render_template('class.html')

@app.route('/grade/<class_id>/grade/<grade_id>', methods=['DELETE'])
@auth_check
def delete_grade_grade(class_id, grade_id):
    return render_template('grade.html')

#Admins
@app.route('/users', methods=['GET'])
@auth_check
def get_users():
    return render_template('users.html')

@app.route('/user', methods=['POST'])
@auth_check
def post_user():
    return render_template('user.html')

@app.route('/user/<id>', methods=['GET'])
@auth_check
def get_user(id):
    return render_template('user.html')

@app.route('/user/<id>', methods=['PUT'])
@auth_check
def put_user(id):
    return render_template('user.html')

@app.route('/user/<id>', methods=['DELETE'])
@auth_check
def delete_user(id):
    return render_template('user.html')

# @app.route('/classes', methods=['GET'])
# @auth_check
# def get_classes():
#     return render_template('classes.html')

@app.route('/class', methods=['POST'])
@auth_check
def post_class():
    return render_template('class.html')

# @app.route('/class/<id>', methods=['GET'])
# @auth_check
# def get_class(id):
#     return render_template('class.html')

@app.route('/class/<id>', methods=['PUT'])
@auth_check
def put_class(id):
    return render_template('class.html')

@app.route('/class/<id>', methods=['DELETE'])
@auth_check
def delete_class(id):
    return render_template('class.html')

@app.route('/teachers', methods=['GET'])
@auth_check
def get_teachers():
    return render_template('teachers.html')

@app.route('/students', methods=['GET'])
@auth_check
def get_students():
    return render_template('students.html')

@app.route('/admins', methods=['GET'])
@auth_check
def get_admins():
    return render_template('admins.html')

@app.route('/parents', methods=['GET'])
@auth_check
def get_parents():
    return render_template('parents.html')

@app.route('/parent/<parent_id>/children', methods=['GET'])
@auth_check
def get_parent_children(parent_id):
    return render_template('parent.html')

@app.route('/parent/<parent_id>/child', methods=['POST'])
@auth_check
def post_parent_child(parent_id):
    return render_template('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['GET'])
@auth_check
def get_parent_child(parent_id, id):
    return render_template('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['PUT'])
@auth_check
def put_parent_child(parent_id, id):
    return render_template('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['DELETE'])
@auth_check
def delete_parent_child(parent_id, id):
    return render_template('parent.html')

@app.route('/teacher/<teacher_id>/class', methods=['POST'])
@auth_check
def post_teacher_class(teacher_id):
    return render_template('teacher.html')

@app.route('/student/<student_id>/class', methods=['POST'])
@auth_check
def post_student_class(student_id):
    return render_template('student.html')

@app.route('/student/<student_id>/payments', methods=['GET'])
@auth_check
def get_student_payments(student_id):
    return render_template('student.html')

@app.route('/student/<student_id>/payment', methods=['POST'])
@auth_check
def post_student_payment(student_id):
    return render_template('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['GET'])
@auth_check
def get_student_payment(student_id, id):
    return render_template('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['PUT'])
@auth_check
def put_student_payment(student_id, id):
    return render_template('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['DELETE'])
@auth_check
def delete_student_payment(student_id, id):
    return render_template('student.html')

@app.route('/notification', methods=['POST'])
@auth_check
def post_notification():
    return render_template('notification.html')

@app.route('/notification/<user_id>', methods=['POST'])
@auth_check
def post_notification_to_user(user_id):
    return render_template('notification.html')
