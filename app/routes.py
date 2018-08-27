from app import app
from flask import request, jsonify, session, make_response
import hashlib, uuid
import os
import binascii
from functools import wraps
import sys

sys.path.insert(0, 'app/services')
from dbservice import *

def jres(s, type='message'):
    return jsonify({type:s})

def get_user_from_session(sessionid):
    stored_session = load_session(sessionid)
    return load_user(stored_session['username'])

def insert_non_empty_in_dict(d, l):
    for i,j in l:
        if j is not None and len(j) > 0:
            d[i]=j

def admin_check(fun):
    @wraps(fun)
    def wrapped(*args, **kwargs):
        user = get_user_from_session(request.cookies['sessionid'])
        if user['type'] == 'admin':
            return fun(*args, **kwargs)
        return jres('Permission denied', type='error'), 403
    return wrapped

def parent_check(fun):
    @wraps(fun)
    def wrapped(*args, **kwargs):
        user = get_user_from_session(request.cookies['sessionid'])
        if user['type'] == 'parent':
            return fun(*args, **kwargs)
        return jres('Permission denied', type='error'), 403
    return wrapped

def teacher_check(fun):
    @wraps(fun)
    def wrapped(*args, **kwargs):
        user = get_user_from_session(request.cookies['sessionid'])
        if user['type'] == 'teacher':
            return fun(*args, **kwargs)
        return jres('Permission denied', type='error'), 403
    return wrapped

def auth_check(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        try:
            sessionid = request.cookies['sessionid']
        except:
            return jres('authetication required')

        stored_session = load_session(sessionid)

        if stored_session is not None and stored_session['sessionid'] == sessionid:
            username = stored_session['username']
            return fun(*args, **kwargs)
        return jres('Invalid session', type='error'), 403
    return wrapper

@app.route('/')
def index():
    return jres('working', type='status')

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
            response = make_response(jres('login successful'))

            response.set_cookie('sessionid', value=sessionid, httponly=True) # secure=True,
            return response

    return jres('Invalid username or password!', type='error')

@app.route('/logout', methods=['GET'])
@auth_check
def logout():
    sessionid = request.cookies['sessionid']
    remove_session(sessionid)
    session.pop(sessionid, None)
    return jres('log out successful')

# @app.route('/home', methods=['GET'])
# @auth_check
# def home():
#     sessionid = request.cookies['sessionid']
#     stored_session = load_session(sessionid)
#     username = stored_session['username']
#     links = [("/profile", "Profile"), ("/appointments", "Appointments"), ("/notifications", "Notifications"), ("/logout", "Log out")]
#     return jsonify(links)
#All
@app.route('/profile', methods=['GET'])
@auth_check
def get_profile():
    user = get_user_from_session(request.cookies['sessionid'])
    return jsonify(user['profile'])

# @app.route('/profile/<username>', methods=['GET'])
# @auth_check
# def get_public_profile(username):
#     user = load_user(username)
#     return jsonify(user['profile'])

@app.route('/edit/profile/', methods=['PUT'])
@auth_check
def put_edit_profile():
    user = get_user_from_session(request.cookies['sessionid'])

    username = user['username']
    is_admin = user['type'] == 'admin'

    try:
        data = {}

        if(is_admin):
            insert_non_empty_in_dict(data, [(x,request.form[x]) for x in ['name', 'surname', 'birthdate']])

        insert_non_empty_in_dict(data, [(x,request.form[x]) for x in ['address', 'email', 'phone']])

        update_user_profile(username, data)
    except:
        return jsonify('profile_edit.html', profile=user['profile'], message='Input error', is_admin=True)

    return jres('profile updated')

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

    return jres('profile updated')

@app.route('/appointments', methods=['GET'])
@auth_check
def get_appointments():
    user = get_user_from_session(request.cookies['sessionid'])

    appointments = load_appointments(user['profile']['email'])
    if appointments is None:
        return jres('no appointments found'), 404
    return jsonify([x for x in appointments])

@app.route('/appointment', methods=['POST'])
@auth_check
def post_appointment():
    data = request.form
    user = get_user_from_session(request.cookies['sessionid'])

    store_appointment(sender=user['profile']['email'], receiver=data['receiver'],
                      date=data['date'], topic=data['topic'], time=data['time'])
    return jres('appointment posted correctly')

@app.route('/appointment/<id>', methods=['GET'])
@auth_check
def get_appointment(id):
    user = get_user_from_session(request.cookies['sessionid'])

    appointment = load_appointment(number=int(id), email=user['profile']['email'])
    if appointment is None:
        return jres('appointment not found', 404)
    return jsonify(appointment)

@app.route('/edit/appointment/<id>', methods=['PUT'])
@auth_check
def put_appointment(id):
    user = get_user_from_session(request.cookies['sessionid'])

    appointment = load_appointment(number=int(id), email=user['profile']['email'])
    if appointment is None:
        return jres('you cannot edit this appointment', type='error')
    edit_appointment(number=int(id), sender=user['profile']['email'], receiver=data['receiver'],
                     date=data['date'], topic=data['topic'], time=data['time'])
    return jres('appointment updated')

@app.route('/appointment/<id>', methods=['DELETE'])
@auth_check
def delete_appointment(id):
    user = get_user_from_session(request.cookies['sessionid'])

    appointment = load_appointment(number=int(id), email=user['profile']['email'])
    if appointment is None or user['profile']['email'] != appointment['sender']:
        return jres('you cannot remove this appointment', type='error')
    remove_appointment(number=int(id))
    return jsonify('appointment removed')

@app.route('/notifications', methods=['GET'])
@auth_check
def get_notifications():
    notifications = load_notifications()
    if notifications is None:
        return jres('no notifications found'), 404
    return jsonify([x for x in notifications])

@app.route('/notification/<id>', methods=['GET'])
@auth_check
def get_notification(id):
    notification = load_notification(id)
    if notification is None:
        return jres('notificatin not found', type='error'), 404
    return jsonify(notification)

#Parents
@app.route('/children', methods=['GET'])
@auth_check
@parent_check
def get_children():
    username = get_user_from_session(request.cookies['sessionid'])
    children = load_children(username)
    if children is None:
        return jres('No children found'), 404
    return jsonify(children)

@app.route('/child/<id>/profile', methods=['GET'])
@auth_check
@parent_check
def get_child_profile(id):
    user = get_user_from_session(request.cookies['sessionid'])
    child = load_child(user, id)
    if child is None:
        return jres('No child found'), 404
    return jsonify(child['profile'])

@app.route('/child/<id>/profile', methods=['PUT'])
@auth_check
@parent_check
def put_child_profile(id):
    user = get_user_from_session(request.cookies['sessionid'])
    child = load_child(user, id)
    try:
        data = {}

        insert_non_empty_in_dict(data, [(x,request.form[x]) for x in ['address', 'email', 'phone']])

        update_user_profile(child['username'], data)
    except:
        return jres('Input error', type='error')

    return jres('profile updated')

@app.route('/child/<id>/grades', methods=['GET'])
@auth_check
@parent_check
def get_child_grades(id):
    user = get_user_from_session(request.cookies['sessionid'])
    grades = load_child_grades(user, id)
    if grades is None:
        return jres('No grades found'), 404
    return jsonify([x for x in grades])

@app.route('/child/<id>/classes', methods=['GET'])
@auth_check
@parent_check
def get_child_classes(id):
    user = get_user_from_session(request.cookies['sessionid'])
    classes = load_child_grades(user, id)
    if classes is None:
        return jres('No classes found'), 404
    return jsonify([x for x in classes])

@app.route('/payments', methods=['GET'])
@auth_check
@parent_check
def get_payments_all():
    user = get_user_from_session(request.cookies['sessionid'])
    payments = load_payments(user)
    if payments is None:
        return jres('No payments found'), 404
    return jsonify([x for x in payments])

@app.route('/payments/history', methods=['GET'])
@auth_check
@parent_check
def get_payments_history():
    user = get_user_from_session(request.cookies['sessionid'])
    payments = load_payments(user, status='paid')
    if payments is None:
        return jres('No payments found'), 404
    return jsonify([x for x in payments])

@app.route('/payments/due', methods=['GET'])
@auth_check
@parent_check
def get_payments_due():
    user = get_user_from_session(request.cookies['sessionid'])
    payments = load_payments(user, status='due')
    if payments is None:
        return jres('No payments found'), 404
    return jsonify([x for x in payments])

@app.route('/payment/<id>', methods=['GET'])
@auth_check
@parent_check
def get_payment(id):
    user = get_user_from_session(request.cookies['sessionid'])
    payment = load_payment(user, id)
    if payment is None:
        return jres('No payment found'), 404
    return jsonify(payment)

@app.route('/payment/<id>', methods=['POST'])
@auth_check
@parent_check
def post_payment(id):
    user = get_user_from_session(request.cookies['sessionid'])
    payment = pay_payment(user, id)
    if payment is None:
        return jres('No payment found'), 404
    return jres('payment was successful')

#Teachers
@app.route('/classes', methods=['GET'])
@auth_check
@teacher_check
def get_classes():
    user = get_user_from_session(request.cookies['sessionid'])
    classes = find_classes(user)
    if classes is None:
        return jres('No class found'), 404
    return jsonify(classes)

@app.route('/class/<id>', methods=['GET'])
@auth_check
@teacher_check
def get_class(id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user, id)
    if _class is None:
        return jres('No class found'), 404
    return jsonify(_class)

@app.route('/class/<id>/grades', methods=['GET'])
@auth_check
@teacher_check
def get_class_grades(id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user, id)
    if _class is None or len(_class['grades']) < 0:
        return jres('No grades found'), 404
    return jsonify(_class['grades'])

@app.route('/class/<id>/grade', methods=['POST'])
@auth_check
@teacher_check
def post_class_grade(id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user, id)
    if _class is None:
        return jres('No class found'), 404
    try:
        store_grade(user, id, request.form['mark'], request.form['childid'], request.form['description'])
    except:
        return jres('Error storing the grade', type='error')
    return jsonify(_class['grades'])

@app.route('/class/<class_id>/grade/<grade_id>', methods=['PUT'])
@auth_check
@teacher_check
def put_class_grade(class_id, grade_id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user, class_id)
    if _class is None:
        return jres('No class found'), 404
    try:
        update_grade(user, class_id, grade_id, request.form['mark'], request.form['childid'], request.form['description'])
    except:
        return jres('Error storing the grade', type='error')
    return jsonify(_class['grades'])

@app.route('/grade/<class_id>/grade/<grade_id>', methods=['DELETE'])
@auth_check
@teacher_check
def delete_grade_grade(class_id, grade_id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user, class_id)
    if _class is None:
        return jres('No class found'), 404
    try:
        delete_grade(user, class_id, grade_id)
    except:
        return jres('Error storing the grade', type='error')
    return jsonify(_class['grades'])

#Admins
@app.route('/users', methods=['GET'])
@auth_check
@admin_check
def get_users():
    users = load_all_users()
    if users is None:
      return jres('No user found', type='error')
    return jsonify(users)

@app.route('/user', methods=['POST'])
@auth_check
@admin_check
def post_user():
    try:
      username = request.form["username"]
      user = load_user(username)
      if user is not None:
          return jres('username already exists', type='error')
      password = request.form["password"]
      type     = request.form["type"]
      salt = str(binascii.hexlify(os.urandom(10)).decode())
      pwdhash = hashlib.sha256(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
      insert_user(username, {'pwdhash':pwdhash, 'salt':salt, 'type':type})
    except Exception as e:
      return jres('Error creating user: '+ str(e.args), type='error')
    return jres('User created successfuly')

@app.route('/user/<id>', methods=['GET'])
@auth_check
@admin_check
def get_user(id):
    user = load_user_by_id(id)
    if user is None:
      return jres('User not found', type='error')
    return jsonify(user)

@app.route('/user/<id>', methods=['PUT'])
@auth_check
@admin_check
def put_user(id):
    user = load_user_by_id(id)
    if user is None:
        return jres('No user found', type='error')

    try:
      username = request.form["username"]
      password = request.form["password"]
      type     = request.form["type"]
      salt = str(binascii.hexlify(os.urandom(10)).decode())
      pwdhash = hashlib.sha256(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
      insert_user(username, {'pwdhash':pwdhash, 'salt':salt, 'type':type})
    except Exception as e:
      return jres('Error creating user: '+ str(e.args), type='error')
    return jres('User updated successfuly')

@app.route('/user/<id>/profile', methods=['PUT'])
@auth_check
@admin_check
def put_user_profile(id):
    user = load_user_by_id(id)
    if user is None:
        return jres('No user found', type='error')
    try:
      update_user_profile(user['username'], request.form)

    except Exception as e:
      return jres('Error updating profile: '+ str(e.args), type='error')
    return jres('User created successfuly')

@app.route('/user/<id>', methods=['DELETE'])
@auth_check
@admin_check
def delete_user(id):

    users = load_user_by_id(id)
    if users is None:
      return jres('No user found', type='error')

    if remove_user(id):
        return jres('succes', type='message')
    else:
        return jres('failed', type='error')

@app.route('/classes', methods=['GET'])
@auth_check
@admin_check
def get_all_classes():
    classes  = load_all_classes()
    if classes is None:
        return jres('No class found'), 404
    return jsonify(classes)

@app.route('/class', methods=['POST'])
@auth_check
@admin_check
def post_class():
    try:
        teacher = request.form['teacher']
        schedule = request.form['schedule']
    except:
        return jres('Error', type='error')

    return jres('success')

@app.route('/class/<id>', methods=['GET'])
@auth_check
@admin_check
def get_class_admin(id):
    _class  = get_class(id, 'admin')
    if _class is None:
        return jres('No class found'), 404
    return jsonify(_class)

@app.route('/class/<id>', methods=['PUT'])
@auth_check
@admin_check
def put_class(id):
    return jsonify('class.html')

@app.route('/class/<id>', methods=['DELETE'])
@auth_check
@admin_check
def delete_class(id):
    return jsonify('class.html')

@app.route('/teachers', methods=['GET'])
@auth_check
@admin_check
def get_teachers():
    return jsonify('teachers.html')

@app.route('/students', methods=['GET'])
@auth_check
@admin_check
def get_students():
    return jsonify('students.html')

@app.route('/admins', methods=['GET'])
@auth_check
@admin_check
def get_admins():
    return jsonify('admins.html')

@app.route('/parents', methods=['GET'])
@auth_check
@admin_check
def get_parents():
    return jsonify('parents.html')

@app.route('/parent/<parent_id>/children', methods=['GET'])
@auth_check
@admin_check
def get_parent_children(parent_id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child', methods=['POST'])
@auth_check
@admin_check
def post_parent_child(parent_id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['GET'])
@auth_check
@admin_check
def get_parent_child(parent_id, id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['PUT'])
@auth_check
@admin_check
def put_parent_child(parent_id, id):
    return jsonify('parent.html')

@app.route('/parent/<parent_id>/child/<id>', methods=['DELETE'])
@auth_check
@admin_check
def delete_parent_child(parent_id, id):
    return jsonify('parent.html')

@app.route('/teacher/<teacher_id>/class', methods=['POST'])
@auth_check
@admin_check
def post_teacher_class(teacher_id):
    return jsonify('teacher.html')

@app.route('/student/<student_id>/class', methods=['POST'])
@auth_check
@admin_check
def post_student_class(student_id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payments', methods=['GET'])
@auth_check
@admin_check
def get_student_payments(student_id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment', methods=['POST'])
@auth_check
@admin_check
def post_student_payment(student_id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['GET'])
@auth_check
@admin_check
def get_student_payment(student_id, id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['PUT'])
@auth_check
@admin_check
def put_student_payment(student_id, id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['DELETE'])
@auth_check
@admin_check
def delete_student_payment(student_id, id):
    return jsonify('student.html')

@app.route('/notification', methods=['POST'])
@auth_check
@admin_check
def post_notification():
    return jsonify('notification.html')

@app.route('/notification/<user_id>', methods=['POST'])
@auth_check
@admin_check
def post_notification_to_user(user_id):
    return jsonify('notification.html')
