from app import mongo



ROLES = []


def all_roles():
    query = mongo.db.auth_user_roles.find({})
    
    global ROLES
    for row in query:
        ROLES.append(row)

all_roles()
