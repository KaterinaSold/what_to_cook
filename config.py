import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or ('postgresql://postgres:cat@localhost/nutrition_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig:
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or ('postgresql://postgres:cat@localhost/nutrition_db_test')