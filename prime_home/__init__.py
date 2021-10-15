from flask import Blueprint


bp_prime_home = Blueprint('prime_home', __name__, template_folder='templates', static_folder='static',\
    static_url_path='/prime_home/static')


from . import views