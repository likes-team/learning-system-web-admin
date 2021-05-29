from mongoengine.connection import connect
from mongoengine.document import Document
from mongoengine.fields import BinaryField, BooleanField, DateTimeField, EmailField, IntField, ListField, StringField
from datetime import datetime
import json


connect("mongo-db")

# Remove collection document field 
mongo.db.lms_registrations.update(
    {'active': True},
    {'$unset': {'book': ''}}
    )
