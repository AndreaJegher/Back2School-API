from pymongo import MongoClient, ASCENDING
from datetime import date
client = MongoClient('localhost', 27017)
db = client.back2school

users    = db.users
grades   = db.grades
classes  = db.classes
payments = db.payments
sessions = db.sessions
appointments = db.appointments
notifications   = db.notifications
sequences = db.sequences

users.create_index([('username', ASCENDING)], unique=True)
users.create_index([('number', ASCENDING)], unique=True)
users.create_index([('profile.email', ASCENDING)], unique=True, sparse=True)

classes.create_index([('number', ASCENDING)], unique=True)
appointments.create_index([('number', ASCENDING)], unique=True)
notifications.create_index([('number', ASCENDING)], unique=True)

def getNextSequence(collection):
    cursor = sequences.find({collection:{'$gt':-1}})
    if cursor.count() < 1:
        sequences.insert({collection:0})
        return 0
    else:
        value = cursor.next()[collection] + 1
        sequences.find_one_and_update(
            {collection:value-1},
            {'$set':{collection:value+1}}
        )
        return value

def load_user_by_id(id):
    try:
        id = int(id)
    except:
      return None

    cursor = users.find({'number':id}, {'_id':0})
    if cursor.count() < 1:
        return None
    return cursor.next()

def remove_user(id):
    try:
        id = int(id)
    except:
      return False
    users.remove({'number':id})
    return True

def load_user(username):
    #cursor = users.find({'username':username}, {'_id':0})
    cursor = users.find({'username':username})
    if cursor.count() < 1:
        return None
    return cursor.next()

def load_all_users():
    cursor = users.find({}, {'_id':0})
    if cursor.count() < 1:
        return None

    return list(cursor)

def insert_user(username, data):
    data ['number']    = getNextSequence('users')
    data ['username']  = username
    users.find_one_and_update(
        {'username':username},
        {'$set':{key: data[key] for key in data}},
        upsert=True
    )

def update_user_profile(username, data):
    users.find_one_and_update(
        {'username':username},
        {'$set':{'profile.'+key: data[key] for key in data}}
    )

def load_session(sessionid):
    cursor = sessions.find({'sessionid':sessionid})
    if cursor.count() < 1:
        return None
    return cursor.next()

def store_session(username, sessionid):
    sessions.find_one_and_update(
        { 'username' : username },
        { '$set' : {'sessionid' : sessionid} },
        upsert=True
    )

def remove_session(sessionid):
    sessions.find_one_and_delete({'sessionid':sessionid})

def load_children(parent):
    parent_full = load_user(parent)
    parent_id = parent["number"]
    #cursor = children.find({'parents': parent_id})
    cursor = users.find({'parents': parent_id})
    #for id in cursor:

    if cursor.count() < 1:
        return None

    return list(cursor)

def load_child(parent, id):
    child = load_user_by_id(id)
    if parent is None:
        raise Exception("Parent not found")
    children = parent["children"]
    try:
        if (int(id) in children):
            return child
    except:
        return None

def load_users_by_type(usertype):
    cursor = users.find({'utype': usertype})
    if cursor.count() < 1:
        return None
    return list(cursor)


def load_appointments(email):
    cursor = appointments.find({'$or':[{'receiver':email}, {'sender':email}]}, {'_id':0})
    if cursor.count() < 1:
        return None
    return cursor

def store_appointment(sender, receiver, date, topic, time):
    number = getNextSequence('appointments')
    appointments.insert({'number':number, 'sender':sender, 'receiver':receiver, 'date':date, 'time':time, 'topic':topic})

def load_appointment(number, email):
    cursor = appointments.find({'number':number, '$or':[{'receiver':email}, {'sender':email}]}, {'_id':0})
    if cursor.count() < 1:
        return None
    return cursor.next()

def edit_appointment(number, sender, receiver, date, topic, time):
    appointments.find_one_and_update(
        {'number': number},
        {'$set' : {'sender':sender, 'receiver':receiver, 'date':date, 'time':time, 'topic':topic}}
    )

def remove_appointment(number):
    appointments.find_one_and_delete({'number':number})

def load_notifications():
    cursor = notifications.find({}, {'_id':0})
    if cursor.count() < 1:
        return None
    return cursor

def load_notification(number):
    cursor = notifications.find({number:'number'}, {'_id':0})
    if cursor.count() < 1:
        return None
    return cursor


###### CLASSES ###############

def insert_class(teacher, students, days,
    hours, classname):
    # print(str(students))
    # print(str(days))
    wresult = classes.insert({
        'number':getNextSequence('classes'),
        'name': classname,
        'teacher':teacher,
        'students':students,
        'schedule': {'days':days, 'hours': hours}})

    # if wresult['writeConcernError'] is not None:
    #     raise Exception('error code: ' + str(wresult['writeConcernError']['code'])
    #         + " msg: " + str(wresult['writeConcernError']['errmsg']))

def load_all_classes():
    cursor = classes.find({}, {'_id':0})
    if cursor.count() < 1:
        return None
    return list(cursor)

def find_classes(teacher_username):
    cursor = classes.find({'teacher': teacher_username}, {'_id':0})
    if cursor.count() < 1:
        return None
    return list(cursor)

def find_class(teacher_username, class_id):
    cursor = classes.find({'teacher': teacher_username, 'number': int(class_id)})
    #print(str(teacher_username) + " " + str(int(class_id)))
    if cursor.count() < 1:
        return None
    _class = cursor.next()
    #print(_class)
    return _class

def get_class_by_name(classname):
    cursor = classes.find({'name': classname})
    if cursor.count() < 1:
        return None
    _class = {}
    _class = cursor.next()
    #raise Exception('E: ' + str(_class))
    return _class

def get_grades_in_class(name):
    print(name)
    cursor = grades.find({'class': name})
    if cursor.count() < 1:
        return None
    return list(cursor)

def store_grade(classname, grade, student_uname):
    number = getNextSequence('grades')
    today = date.today()
    grades.insert({'number':number, 'class':classname, 'student':student_uname, 'date': str(today), 'grade': int(grade)})

def load_child_grades(student, _class):
    if _class is None:
        cursor = grades.find({'student': student})
    else:
        cursor = grades.find({'student': student, 'class': _class})
    if cursor.count() < 1:
        return None
    return list(cursor)

def load_child_classes(student):
    cursor = classes.find({'students': student})
    if cursor.count() < 1:
        return None
    return list(cursor)

def delete_grade(classname, grade_id):
    grades.find_one_and_delete({'number':int(grade_id), 'class': classname})


def load_payments(student_id, status):
    if status is not None:
        cursor = payments.find({'userid': int(student_id), 'pstatus': status})
    else:
        cursor = payments.find({'userid': int(student_id)})
    if cursor.count() < 1:
        return None
    return list(cursor)

def load_user_payment(user_id, payment_id):
    cursor = payments.find({'userid': int(user_id), 'number': int(payment_id)})
    if cursor.count() < 1:
        return None
    return cursor.next()

def create_payment_for_student(userid, dueDate, amount):
    sequence = sequences.find({'payments': {'$exists':'true'}})
    student_id = int(userid)
    p = sequence.next()
    wresult = payments.insert({
    '_id': (p['payments']),
    'number': (p['payments']),
    'pstatus': 'due',
    'dueDate': dueDate,
    'userid': student_id,
    'amount': amount })

    sequences.find_one_and_update({'_id': p['_id']}, {'$set':{'payments': (int(p['payments']) + 1)}})

def delete_payment_for_user(user_id, payment_id):
    payments.find_one_and_delete({'number':payment_id, 'userid': user_id})

def pay_payment(userid, paymentid):
    query = {'number': int(payment_id), 'userid': int(userid), 'pstatus': 'due'}
    new_values = {'$set': {'pstatus': 'completed'}}
    cursor = payments.find_one(query)
    p = cursor.next()
    if p is not None:
        payments.update_one(query, new_values)
        return p
    else:
        return None
