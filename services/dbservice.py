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

def load_session(username):
    cursor = sessions.find({'username':username})
    if cursor.count() < 1:
        return None
    return cursor.next()

def store_session(username, sessionid):
    sessions.find_one_and_update(
        {'username':username},
        {'sessionid':sessionid},
        upsert=True
    )
