from decimal import Decimal



def format_to_str_php(number, replacement='0.00'):
    if isinstance(number, str):
        return replacement

    if isinstance(number, Decimal):
        return "{:.2f}".format(number)
    return "{:.2f}".format(Decimal(str(number)))


def convert_decimal128_to_decimal(number):
    if number is None:
        return Decimal('0.00')
    return Decimal(str(number))