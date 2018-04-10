from app import app
from flask import request, jsonify, session, make_response
import hashlib, uuid
import os
import binascii
from functools import wraps
from services.dbservice import *

def jresponse(s, type='message'):
    return jsonify({type:s})

def auth_check(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        try:
            sessionid = request.cookies['sessionid']
        except:
            return jresponse('authetication required')

        stored_session = load_session(sessionid)

        if stored_session is not None and stored_session['sessionid'] == sessionid:
            username = stored_session['username']
            return fun(*args, **kwargs)
        return jresponse('Invalid session', type='error')
    return wrapper

@app.route('/')
def index():
    return jresponse('working', type='status')

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
            response = make_response(jresponse('login successful'))

            response.set_cookie('sessionid', value=sessionid, secure=True, httponly=True)
            return response

    return jresponse('Invalid username or password!', type='error')

@app.route('/logout', methods=['GET'])
@auth_check
def logout():
    sessionid = request.cookies['sessionid']
    remove_session(sessionid)
    session.pop(sessionid, None)
    return jresponse('log out successful')

@app.route('/home', methods=['GET'])
@auth_check
def home():
    sessionid = request.cookies['sessionid']
    stored_session = load_session(sessionid)
    username = stored_session['username']
    links = [("/profile", "Profile"), ("/appointments", "Appointments"), ("/notifications", "Notifications"), ("/logout", "Log out")]
    return jsonify(links)

def insert_non_empty_in_dict(d, l):
    for i,j in l:
        if j is not None and len(j) > 0:
            d[i]=j

#All
@app.route('/profile', methods=['GET'])
@auth_check
def get_profile():
    stored_session = load_session(request.cookies['sessionid'])
    user = load_user(stored_session['username'])
    return jsonify(user['profile'])

@app.route('/profile/<username>', methods=['GET'])
@auth_check
def get_public_profile(username):
    user = load_user(username)
    return jsonify(user['profile'])

@app.route('/edit/profile/', methods=['PUT'])
@auth_check
def put_edit_profile():
    stored_session = load_session(request.cookies['sessionid'])
    user = load_user(stored_session['username'])
    username = user['username']
    is_admin = True

    try:
        data = {}

        if(is_admin):
            insert_non_empty_in_dict(data, [(x,request.form[x]) for x in ['name', 'surname', 'birthdate']])

        insert_non_empty_in_dict(data, [(x,request.form[x]) for x in ['address', 'email', 'phone']])

        print (username, data)
        update_user_profile(username, data)
    except:
        return jsonify('profile_edit.html', profile=user['profile'], message='Input error', is_admin=True)

    return jresponse('profile updated')

@app.route('/edit/profile/<username>', methods=['PUT'])
@auth_check
def put_edit_user_profile(username):
    is_admin = True
    try:
        data = {}

        if(is_admin):
            insert_non_empty_in_dict(data, [(x,request.form[x]) for x in ['name', 'surname', 'birthdate']])

        insert_non_empty_in_dict(data, [(x,request.form[x]) for x in ['address', 'email', 'phone']])

        print (username, data)
        update_user_profile(username, data)
    except:
        return jsonify('profile_edit.html', profile=user['profile'], message='Input error', is_admin=True)

    return jresponse('profile updated')

@app.route('/appointments', methods=['GET'])
@auth_check
def get_appointments():
    stored_session = load_session(request.cookies['sessionid'])
    user = load_user(stored_session['username'])
    appointments = load_appointments(user['profile']['email'])
    return jsonify(appointments)

@app.route('/appointment', methods=['POST'])
@auth_check
def post_appointment():
    data = request.form
    stored_session = load_session(request.cookies['sessionid'])
    user = load_user(stored_session['username'])
    store_appointment(sender=user['profile']['email'], receiver=data['receiver'],
                      date=data['date'], topic=data['topic'], time=data['time'])
    return jresponse('appointment posted correctly')

@app.route('/appointment/<id>', methods=['GET'])
@auth_check
def get_appointment(id):
    stored_session = load_session(request.cookies['sessionid'])
    user = load_user(stored_session['username'])
    appointment = load_appointment(number=int(id), email=user['profile']['email'])
    can_edit = user['profile']['email'] == appointment['sender']
    return jsonify(appointment)

@app.route('/edit/appointment/<id>', methods=['GET'])
@auth_check
def get_appointment_edit(id):
    stored_session = load_session(request.cookies['sessionid'])
    user = load_user(stored_session['username'])
    appointment = load_appointment(number=int(id), email=user['profile']['email'])
    return jsonify(appointment)

@app.route('/appointment/<id>', methods=['PUT'])
@auth_check
def put_appointment(id):
    return jresponse('appointment updated')

@app.route('/appointment/<id>', methods=['DELETE'])
@auth_check
def delete_appointment(id):
    return jsonify('appointment deleted')

@app.route('/notifications', methods=['GET'])
@auth_check
def get_notifications():
    return jsonify('notifications.html')

@app.route('/notification/<id>', methods=['GET'])
@auth_check
def get_notification(id):
    return jsonify('notification.html')

#Parents
@app.route('/children', methods=['GET'])
@auth_check
def get_children():
    return jsonify('children.html')

@app.route('/child/<id>/profile', methods=['GET'])
@auth_check
def get_child_profile(id):
    return jsonify('child.html')

@app.route('/child/<id>/profile', methods=['PUT'])
@auth_check
def put_child_profile(id):
    return jsonify('child.html')

@app.route('/child/<id>/grades', methods=['GET'])
@auth_check
def get_child_grades(id):
    return jsonify('child.html')

@app.route('/child/<id>/classes', methods=['GET'])
@auth_check
def get_child_classes(id):
    return jsonify('child.html')

@app.route('/payments/all', methods=['GET'])
@auth_check
def get_payments_all():
    return jsonify('payments.html')

@app.route('/payments/history', methods=['GET'])
@auth_check
def get_payments_history():
    return jsonify('payments.html')

@app.route('/payments/due', methods=['GET'])
@auth_check
def get_payments_due():
    return jsonify('payments.html')

@app.route('/payment/<id>', methods=['GET'])
@auth_check
def get_payment(id):
    return jsonify('payment.html')

@app.route('/payment/<id>', methods=['POST'])
@auth_check
def post_payment(id):
    return jsonify('payment.html')

#Teachers
@app.route('/classes', methods=['GET'])
@auth_check
def get_classes():
    return jsonify('classes.html')

@app.route('/class/<id>', methods=['GET'])
@auth_check
def get_class(id):
    return jsonify('class.html')

@app.route('/class/<id>/grades', methods=['GET'])
@auth_check
def get_class_grades(id):
    return jsonify('class.html')

@app.route('/class/<id>/grade', methods=['POST'])
@auth_check
def post_class_grade(id):
    return jsonify('class.html')

@app.route('/class/<class_id>/grade/<grade_id>', methods=['PUT'])
@auth_check
def put_class_grade(class_id, grade_id):
    return jsonify('class.html')

@app.route('/grade/<class_id>/grade/<grade_id>', methods=['DELETE'])
@auth_check
def delete_grade_grade(class_id, grade_id):
    return jsonify('grade.html')

#Admins
@app.route('/users', methods=['GET'])
@auth_check
def get_users():
    return jsonify('users.html')

@app.route('/user', methods=['POST'])
@auth_check
def post_user():
    return jsonify('user.html')

@app.route('/user/<id>', methods=['GET'])
@auth_check
def get_user(id):
    return jsonify('user.html')

@app.route('/user/<id>', methods=['PUT'])
@auth_check
def put_user(id):
    return jsonify('user.html')

@app.route('/user/<id>', methods=['DELETE'])
@auth_check
def delete_user(id):
    return jsonify('user.html')

# @app.route('/classes', methods=['GET'])
# @auth_check
# def get_classes():
#     return jsonify('classes.html')

@app.route('/class', methods=['POST'])
@auth_check
def post_class():
    return jsonify('class.html')

# @app.route('/class/<id>', methods=['GET'])
# @auth_check
# def get_class(id):
#     return jsonify('class.html')

@app.route('/class/<id>', methods=['PUT'])
@auth_check
def put_class(id):
    return jsonify('class.html')

@app.route('/class/<id>', methods=['DELETE'])
@auth_check
def delete_class(id):
    return jsonify('class.html')

@app.route('/teachers', methods=['GET'])
@auth_check
def get_teachers():
    return jsonify('teachers.html')

@app.route('/students', methods=['GET'])
@auth_check
def get_students():
    return jsonify('students.html')

@app.route('/admins', methods=['GET'])
@auth_check
def get_admins():
    return jsonify('admins.html')

@app.route('/parents', methods=['GET'])
@auth_check
def get_parents():
    return jsonify('parents.html')

@app.route('/parent/<parent_id>/children', methods=['GET'])
@auth_check
def get_parent_children(parent_id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child', methods=['POST'])
@auth_check
def post_parent_child(parent_id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['GET'])
@auth_check
def get_parent_child(parent_id, id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['PUT'])
@auth_check
def put_parent_child(parent_id, id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['DELETE'])
@auth_check
def delete_parent_child(parent_id, id):
    return jsonify('parent.html')

@app.route('/teacher/<teacher_id>/class', methods=['POST'])
@auth_check
def post_teacher_class(teacher_id):
    return jsonify('teacher.html')

@app.route('/student/<student_id>/class', methods=['POST'])
@auth_check
def post_student_class(student_id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payments', methods=['GET'])
@auth_check
def get_student_payments(student_id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment', methods=['POST'])
@auth_check
def post_student_payment(student_id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['GET'])
@auth_check
def get_student_payment(student_id, id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['PUT'])
@auth_check
def put_student_payment(student_id, id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['DELETE'])
@auth_check
def delete_student_payment(student_id, id):
    return jsonify('student.html')

@app.route('/notification', methods=['POST'])
@auth_check
def post_notification():
    return jsonify('notification.html')

@app.route('/notification/<user_id>', methods=['POST'])
@auth_check
def post_notification_to_user(user_id):
    return jsonify('notification.html')
