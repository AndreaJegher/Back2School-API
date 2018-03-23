from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.back2school

users    = db.users
grades   = db.grades
classes  = db.classes
payments = db.payments
events   = db.events
sessions = db.sessions

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
