from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.back2school

users    = db.users
grades   = db.grades
classes  = db.classes
payments = db.payments
events   = db.events
sessions = db.sessions
appointments = db.appointments

def load_user(username):
    cursor = users.find({'username':username})
    if cursor.count() < 1:
        return None
    return cursor.next()

def insert_user(username, pwdhash, salt):
    users.insert({'username':username, 'pwdhash':pwdhash, 'salt':salt})

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
    sessions.find_one_and_delete('sessionid':sessionid)

def load_appointments(username):
    cursor = appointments.find({'receiver':username})
    if cursor.count() < 1:
        return None
    return cursor

def store_appointment(sender, receiver, date, topic):
    appointments.find_one_and_update(
        {'sender':sender, 'receiver':receiver, 'date':date},
        {'$set' : {'topic':topic}}
    )

def edit_appointment_date(sender, receiver, date, new_date):
    appointments.find_one_and_update(
        {'sender':sender, 'receiver':receiver, 'date':date},
        {'$set' : {'date':new_date}}
    )

def remove_appointment(sender, receiver, date):
    appointments.find_one_and_delete({'sender':sender, 'receiver':receiver, 'date':date})
