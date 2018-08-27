from pymongo import MongoClient, ASCENDING

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
    cursor = users.find({'username':username}, {'_id':0})
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
    cursor = children.find({'parent':parent})
    if cursor.count() < 1:
        return None

    return list(cursor)

def load_child(parent, id):
    child = load_user_by_id(id)
    parent = load_user(parent)
    try:
        if ( id in parent["profile"]["children"] ):
            return child["profile"]
    except:
        return None

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
        {'number':number},
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

def inser_class(teacher, students, schedule):
    classes.insert({'number':getNextSequence('classes'), 'teacher':teacher, 'students':[], 'schedule':schedule})

def load_all_classes():
    cursor = classes.find({}, {'_id':0})
    if cursor.count() < 1:
        return None

    return list(cursor)
