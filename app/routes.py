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
    user = load_user(stored_session['username'])
    if user is None:
        raise ValueError('user not found')
    return user

def insert_non_empty_in_dict(d, l):
    for i,j in l:
        if j is not None and len(j) > 0:
            d[i]=j

def admin_check(fun):
    @wraps(fun)
    def wrapped(*args, **kwargs):
        user = get_user_from_session(request.cookies['sessionid'])
        if user['utype'] == 'admin':
            return fun(*args, **kwargs)
        return jres('Permission denied: ' + str(user['utype']), type='error'), 403
    return wrapped

def parent_check(fun):
    @wraps(fun)
    def wrapped(*args, **kwargs):
        user = get_user_from_session(request.cookies['sessionid'])
        if user['utype'] == 'parent':
            return fun(*args, **kwargs)
        return jres('Permission denied: ' + str(user['utype']), type='error'), 403
    return wrapped

def teacher_check(fun):
    @wraps(fun)
    def wrapped(*args, **kwargs):
        user = get_user_from_session(request.cookies['sessionid'])
        if user['utype'] == 'teacher':
            return fun(*args, **kwargs)
        return jres('Permission denied: ' + str(user['utype']), type='error'), 403
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
            response = make_response(jres('login successful. Welcome ' + username))

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

    is_admin = user['utype'] == 'admin'

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
    data = request.form
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
    return jres('appointment removed')

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


##############################################################################
#Parents
##############################################################################

@app.route('/children', methods=['GET'])
@auth_check
@parent_check
def get_children():
    username = get_user_from_session(request.cookies['sessionid'])
    children = load_children(username)
    if children is None:
        return jres('No children found'), 404

    for c in children:
        c.pop("_id", None)
    return jsonify(children)
    #return jres(children)

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

@app.route('/child/<name>/grades', methods=['GET'])
@auth_check
@parent_check
def get_child_grades(name):
    user = get_user_from_session(request.cookies['sessionid'])
    child = load_user(name)
    if (int(user['number']) in child['parents']):
        grades = load_child_grades(child['username'], None)
    if grades is None:
        return jres('No grades found'), 404
    for g in grades:
        g.pop('_id', None)
    return jsonify([x for x in grades])

@app.route('/child/<name>/classes', methods=['GET'])
@auth_check
@parent_check
def get_child_classes(name):
    user = get_user_from_session(request.cookies['sessionid'])
    child = load_user(name)
    if (int(user['number']) in child['parents']):
        classes = load_child_classes(child['username'])
    if classes is None:
        return jres('No classes found'), 404
    for c in classes:
        c.pop('_id', None)
    return jsonify([x for x in classes])


###################################################################
###################################################################
###################################################################
@app.route('/payments', methods=['GET'])
@auth_check
@parent_check
def get_payments_all():
    user = get_user_from_session(request.cookies['sessionid'])
    all_payments = []
    if 'children' in user:
        for c in user['children']:
            payments = load_payments(c, None)
            if payments:
                all_payments = all_payments + payments
    if not all_payments:
        return jres('No payments found'), 404
    for p in all_payments:
        if '_id' in p:
            p.pop('_id', None)
    return jsonify(all_payments)

@app.route('/payments/history', methods=['GET'])
@auth_check
@parent_check
def get_payments_history():
    user = get_user_from_session(request.cookies['sessionid'])
    all_payments = []
    if 'children' in user:
        for c in user['children']:
            payments = load_payments(c, status='completed')
            if payments:
                all_payments = all_payments + payments
    if not all_payments:
        return jres('No payments found'), 404
    for p in all_payments:
        if '_id' in p:
            p.pop('_id', None)
    return jsonify(all_payments)

@app.route('/payments/due', methods=['GET'])
@auth_check
@parent_check
def get_payments_due():
    user = get_user_from_session(request.cookies['sessionid'])
    all_payments = []
    if 'children' in user:
        for c in user['children']:
            payments = load_payments(c, status='due')
            if payments:
                all_payments = all_payments + payments
    if not all_payments:
        return jres('No payments found'), 404
    for p in all_payments:
        if '_id' in p:
            p.pop('_id', None)
    return jsonify(all_payments)

@app.route('/child/<childid>/payment/<paymentid>', methods=['GET'])
@auth_check
@parent_check
def get_payment(childid, paymentid):
    user = get_user_from_session(request.cookies['sessionid'])
    if 'children' in user and int(childid) in user['children']:
        payment = load_user_payment(childid, paymentid)
    if payment is None:
        return jres('No payment found'), 404
    if '_id' in payment:
        payment.pop('_id', None)
    return jsonify(payment)

@app.route('/child/<childid>/payment/<paymentid>', methods=['POST'])
@auth_check
@parent_check
def post_payment(childid, paymentid):
    user = get_user_from_session(request.cookies['sessionid'])
    payment = {}
    if 'children' in user and int(childid) in user['children']:
        payment = load_user_payment(childid, paymentid)
    if payment is None:
        return jres('No payment found'), 404
    try:
        payment = pay_payment(childid, paymentid)
        if payment is None:
            raise ValueError('Payment missing')
    except Exception as e:
        jres('Payment was not finalized ' + str(e), 405)
    return jres('payment was successful ' + str(payment), 200)

#Teachers
@app.route('/classes', methods=['GET'])
@auth_check
@teacher_check
def get_classes():
    user = get_user_from_session(request.cookies['sessionid'])
    classes = find_classes(user['username'])
    if classes is None:
        return jres('No class found'), 404
    else:
        for c in classes:
            c.pop('_id', None)
            return jsonify(classes)

@app.route('/class/<id>', methods=['GET'])
@auth_check
@teacher_check
def get_class(id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user['username'], id)
    if _class is None:
        return jres('No class found'), 404
    _class.pop('_id', None)
    #print(str(_class))
    return jsonify(_class)

@app.route('/class/<id>/grades', methods=['GET'])
@auth_check
@teacher_check
def get_class_grades(id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user['username'], id)
    #if _class is None or len(_class['grades']) < 0:
    #    return jres('No grades found'), 404
    if _class is None:
        return jres('Wrong class chosen'), 404
    else:
        grades = get_grades_in_class(_class['name'])
        if grades is None:
            return jres('No grades found'), 404
        for g in grades:
            g.pop('_id', None)
        return jsonify(grades)

@app.route('/class/<id>/grade', methods=['POST'])
@auth_check
@teacher_check
def post_class_grade(id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user['username'], id)
    if _class is None:
        return jres('No class found'), 404
    try:
        store_grade(_class['name'], request.form['grade'], request.form['student'])
    except:
        return jres('Error storing the grade', type='error')
    return jres('Grade stored successfully', 200)

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

@app.route('/class/<class_id>/grade/<grade_id>', methods=['DELETE'])
@auth_check
@teacher_check
def delete_grade_grade(class_id, grade_id):
    user = get_user_from_session(request.cookies['sessionid'])
    _class = find_class(user['username'], class_id)
    if _class is None:
        return jres('No class found'), 404
    try:
        grades = get_grades_in_class(_class['name'])
        for g in grades:
            if int(g["number"]) == int(grade_id):
                delete_grade(_class['name'], grade_id)
    except:
        return jres('Error deleting the grade', type='error')
    grades = get_grades_in_class(_class['name'])
    for g in grades:
        g.pop('_id', None)
    return jsonify(grades)

#########################################################################
#########################################################################
#########################################################################
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
      type     = request.form["utype"]
      salt = str(binascii.hexlify(os.urandom(10)).decode())
      pwdhash = hashlib.sha256(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
      insert_user(username, {'pwdhash':pwdhash, 'salt':salt, 'utype':type})
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
      type     = request.form["utype"]
      salt = str(binascii.hexlify(os.urandom(10)).decode())
      pwdhash = hashlib.sha256(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
      insert_user(username, {'pwdhash':pwdhash, 'salt':salt, 'utype':type})
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

@app.route('/admin/classes', methods=['GET'])
@auth_check
@admin_check
def get_all_classes():
    classes  = load_all_classes()
    if classes is None:
        return jres('No class found'), 404
    for c in classes:
        c.pop('_id', None)
        return jsonify(classes)

@app.route('/admin/class', methods=['POST'])
@auth_check
@admin_check
def post_class():
    try:
        req_data = request.get_json()
        teacher = req_data['teacher']
        days = req_data['days']
        classname = req_data['class']
        students = req_data['students']
        hours = req_data['hours']
        insert_class(teacher, students, days, hours, classname)
    except Exception as e:
        return jres('Error: ' + str(students) + " === " + str(days) + ":::" + str(e), type='error'), 404
    return jres('success')

@app.route('/admin/class/<name>', methods=['GET'])
@auth_check
@admin_check
def get_class_admin(name):
    _class  = get_class_by_name(name)
    if _class is None:
        return jres('No class found'), 404
    _class.pop('_id', None)
    return jsonify(_class)
    #return jres("Whatever " + str(_class))

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

@app.route('/admin/teachers', methods=['GET'])
@auth_check
@admin_check
def get_teachers():
    students = load_users_by_type('teacher')
    if students is None:
        return jres('No teacher was found')
    for s in students:
        s.pop('_id', None)
    return jsonify(students)

@app.route('/admin/students', methods=['GET'])
@auth_check
@admin_check
def get_students():
    students = load_users_by_type('child')
    if students is None:
        return jres('No child was found')
    for s in students:
        s.pop('_id', None)
    return jsonify(students)

@app.route('/admin/admins', methods=['GET'])
@auth_check
@admin_check
def get_admins():
    students = load_users_by_type('admin')
    if students is None:
        return jres('No admin was found')
    for s in students:
        s.pop('_id', None)
    return jsonify(students)

@app.route('/admin/parents', methods=['GET'])
@auth_check
@admin_check
def get_parents():
    students = load_users_by_type('parent')
    if students is None:
        return jres('No parent was found')
    for s in students:
        s.pop('_id', None)
    return jsonify(students)

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
    payments = load_payments(student_id, None)
    if payments is None:
        return jres('No payment was found')
    for p in payments:
        p.pop('_id', None)
    return jsonify(payments)


@app.route('/student/<student_id>/payment', methods=['POST'])
@auth_check
@admin_check
def post_student_payment(student_id):
    req_data = request.get_json()
    dueDate = req_data['dueDate']
    amount = req_data['amount']
    try:
        create_payment_for_student(student_id, dueDate, amount)
    except Exception as e:
        return jres('Error storing the payment ' + str(e), type='error')
    return jres('Payment saved correctly', 200)

@app.route('/student/<student_id>/payment/<id>', methods=['GET'])
@auth_check
@admin_check
def get_student_payment(student_id, id):
    payment = load_user_payment(student_id, id)
    if payments is None:
        return jres('No such payment exists')
    payment.pop('_id', None)
    return jsonify(payment)

@app.route('/student/<student_id>/payment/<id>', methods=['PUT'])
@auth_check
@admin_check
def put_student_payment(student_id, id):
    return jsonify('student.html')

@app.route('/student/<student_id>/payment/<id>', methods=['DELETE'])
@auth_check
@admin_check
def delete_student_payment(student_id, id):
    try:
        delete_payment_for_user(int(id), int(student_id))
    except Exception as e:
        return jres('Error deleting the payment ' + str(e), type='error')
    return jres('Payment deleted correctly', 200)

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
