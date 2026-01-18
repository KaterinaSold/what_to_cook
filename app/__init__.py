from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'

from app.models import User

# Настраиваем user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)

    # Конфигурация
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:cat@db/nutrition_db'
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)

    # Регистрация Blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin_routes import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.user_routes import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    # Главный маршрут
    @app.route('/')
    def index():
        return render_template('index.html')

    # Создание таблиц при первом запуске
    with app.app_context():
        db.create_all()

    return app