from decimal import Decimal



def format_to_str_php(number):
    return "{:.2f}".format(Decimal(str(number)))
