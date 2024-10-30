from flask import Blueprint
from prime_admin.models import PageSettings

bp_prime_home = Blueprint('prime_home', __name__, template_folder='templates', static_folder='static',\
    static_url_path='/prime_home/static')

@bp_prime_home.context_processor
def inject_home_background_image():
    home_background_image = PageSettings.objects.filter(key="home_background_image").first()
    return dict(home_background_image=home_background_image)

from . import views
