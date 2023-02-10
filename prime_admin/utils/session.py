def get_time_by_session(session):
    if session == "1":
        return "FROM 8:00AM TO 11:00AM"
    elif session == "2":
        return "FROM 1:00PM TO 4:00PM"
    elif session == "3":
        return "FROM 6:00PM TO 9:00PM"
    else:
        raise ValueError("InceptionError: Invalid session value")