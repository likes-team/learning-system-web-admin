import os
from dateutil import tz
import pytz
from dotenv import load_dotenv
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont



basedir = os.path.abspath(os.path.dirname(__file__))

TIMEZONE = pytz.timezone('Asia/Manila')
FROM_ZONE = tz.tzutc()

def _register_old_english_font():
    font_path = basedir + '/prime_admin/static/font/black_chancery.TTF'
    pdfmetrics.registerFont(TTFont('Black Chancery', font_path))

def _register_arial_font():
    font_path = basedir + '/prime_admin/static/font/arial.ttf'
    pdfmetrics.registerFont(TTFont('Arial', font_path))


def _register_calibri_font():
    font_path = basedir + '/prime_admin/static/font/CALIBRIB.TTF'
    pdfmetrics.registerFont(TTFont('Calibri', font_path))


def _register_arial_th_font():
    font_path = basedir + '/prime_admin/static/font/ArialTh.ttf'
    pdfmetrics.registerFont(TTFont('ArialTh', font_path))


_register_old_english_font()
_register_arial_font()
_register_calibri_font()
_register_arial_th_font()


class Config(object):
    load_dotenv()

    SECRET_KEY = os.environ.get('SECRET_KEY') # Key

    CORS_HEADERS = 'Content-Type' # Flask Cors
    PDF_FOLDER = basedir + '/prime_admin/static/pdf/'

    # DEVELOPERS-NOTE: ADMIN PAGE CONFIGURATIONS HERE
    ADMIN = {
        'APPLICATION_NAME': 'Likes',
        'DATA_PER_PAGE': 25,
        'MODELS_SIDEBAR_HEADER': 'SYSTEM MODELS'
    }
    #                 -END-

    # DEVELOPERS-NOTE: AUTH CONFIGURATIONS HERE
    AUTH = {
        'LOGIN_REDIRECT_URL': 'lms.dashboard',
    }
    #                 -END-


class DevelopmentConfig(Config):
    """
    Development configurations
    """
    MONGO_URI = os.environ.get('MONGO_URI_DEV')
    MONGODB_HOST = os.environ.get('MONGO_URI_DEV')
    DEBUG = True


class ProductionConfig(Config):
    """
    Production configurations
    """
    MONGO_URI = os.environ.get('MONGO_URI_PROD')
    MONGODB_HOST = os.environ.get('MONGO_URI_PROD')
    DEBUG = False


class TestingConfig(Config):
    """
    Testing configurations
    """

    TESTING = True
    # SQLALCHEMY_ECHO = True


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
