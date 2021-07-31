import os
from dateutil import tz
import pytz
from dotenv import load_dotenv



basedir = os.path.abspath(os.path.dirname(__file__))

TIMEZONE = pytz.timezone('Asia/Manila')
FROM_ZONE = tz.tzutc()


class Config(object):
    load_dotenv()

    SECRET_KEY = os.environ.get('SECRET_KEY') # Key

    CORS_HEADERS = 'Content-Type' # Flask Cors

    # DEVELOPERS-NOTE: ADMIN PAGE CONFIGURATIONS HERE
    ADMIN = {
        'APPLICATION_NAME': 'Likes',
        'DATA_PER_PAGE': 25,
        'HOME_URL': 'bp_admin.dashboard',
        'DASHBOARD_URL': 'bp_admin.dashboard',
        'MODELS_SIDEBAR_HEADER': 'SYSTEM MODELS'
    }
    #                 -END-

    # DEVELOPERS-NOTE: AUTH CONFIGURATIONS HERE
    AUTH = {
        'LOGIN_REDIRECT_URL': 'lms.dashboard',
    }
    #                 -END-

    # DEVELOPERS-NOTE: -ADD YOUR CONFIGURATIONS HERE-
    
    #                 -END-


class DevelopmentConfig(Config):
    """
    Development configurations
    """

    MONGODB_HOST = "mongodb+srv://dbUser:dbUserPassword@cluster0.hfnwc.mongodb.net/primeTestDB?retryWrites=true&w=majority"

    MONGO_URI = "mongodb+srv://dbUser:dbUserPassword@cluster0.hfnwc.mongodb.net/primeTestDB?retryWrites=true&w=majority"

    DEBUG = True

class ProductionConfig(Config):
    """
    Production configurations
    """

    MONGODB_HOST = "mongodb+srv://dbUser:dbUserPassword@cluster0.hfnwc.mongodb.net/primeDB?retryWrites=true&w=majority"

    MONGO_URI = "mongodb+srv://dbUser:dbUserPassword@cluster0.hfnwc.mongodb.net/primeDB?retryWrites=true&w=majority"

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
