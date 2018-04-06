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

def getNextSequence(collection):
    cursor = collection.find({'sequence':{'$gt':-1}})
    if cursor.count() < 1:
        collection.insert({'sequence':0})
        return 0
    else:
        value = cursor.next()['sequence'] + 1
        collection.find_one_and_update(
            {'sequence':value-1},
            {'$set':{'sequence':value+1}}
        )
        return value

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
    sessions.find_one_and_delete({'sessionid':sessionid})

def load_appointments(email):
    cursor = appointments.find({'$or':[{'receiver':email}, {'sender':email}]}, {'_id':0})
    if cursor.count() < 1:
        return None
    return cursor

def store_appointment(sender, receiver, date, topic, time):
    number = getNextSequence(appointments)
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

def remove_appointment(number, sender):
    appointments.find_one_and_delete({'number':number})
