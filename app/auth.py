from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

bp = Blueprint('auth', __name__)

@bp.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint для входа через модальное окно"""
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Вы уже вошли в систему'})
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    remember = data.get('remember', False)
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Заполните все поля'})
    
    user = User.query.filter_by(email=email).first()
    
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({'success': False, 'message': 'Неверный email или пароль'})
    
    login_user(user, remember=remember)
    return jsonify({'success': True, 'message': f'Добро пожаловать, {user.username}!'})

@bp.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint для регистрации через модальное окно"""
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Вы уже вошли в систему'})
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password2 = data.get('password2')
    
    # Валидация
    if not all([username, email, password, password2]):
        return jsonify({'success': False, 'message': 'Заполните все поля'})
    
    if len(username) < 2 or len(username) > 64:
        return jsonify({'success': False, 'message': 'Имя пользователя должно быть от 2 до 64 символов'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Пароль должен быть не менее 6 символов'})
    
    if password != password2:
        return jsonify({'success': False, 'message': 'Пароли не совпадают'})
    
    # Проверка существующих пользователей
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Это имя пользователя уже занято'})
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Этот email уже зарегистрирован'})
    
    # Создание пользователя
    user = User(username=username, email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Автоматический вход после регистрации
    login_user(user)
    return jsonify({'success': True, 'message': f'Регистрация успешна! Добро пожаловать, {username}!'})

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@bp.route('/login')
def login_redirect():
    """Редирект со старого URL логина"""
    return redirect(url_for('index'))

@bp.route('/register')
def register_redirect():
    """Редирект со старого URL регистрации"""
    return redirect(url_for('index'))