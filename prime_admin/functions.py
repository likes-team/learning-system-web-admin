from datetime import datetime



def generate_number(date_now, lID):
    generated_number = ""

    if 1 <= lID < 9:
        generated_number = str(date_now.year) + '%02d' % date_now.month +"000" + str(lID+1)
    elif 9 <= lID < 99:
        generated_number = str(date_now.year) + '%02d' %  date_now.month + "00" + str(lID+1)
    elif 999 <= lID < 9999:
        generated_number = str(date_now.year) + '%02d' % date_now.month + "0" + str(lID+1)
    else:
        generated_number = str(date_now.year) + '%02d' % date_now.month + str(lID+1)
 
    return generated_number


def generate_employee_id(lID):
    generated_number = ""

    if 0 <= lID < 9:
        generated_number = "PLI" +"000" + str(lID+1)
    elif 9 <= lID < 99:
        generated_number = "PLI" + "00" + str(lID+1)
    elif 999 <= lID < 9999:
        generated_number = "PLI" + "0" + str(lID+1)
    else:
        generated_number = "PLI" + str(lID+1)
 
    return generated_number