#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Использование: python init_db.py [--drop]
"""

import sys
import argparse
from app import create_app, db
from app.models import User, Ingredient

def init_database(drop_all=False):
    """Инициализация базы данных"""
    app = create_app()
    
    with app.app_context():
        if drop_all:
            print("Удаление всех таблиц...")
            db.drop_all()
        
        print("Создание таблиц...")
        db.create_all()
        
        # Проверяем, есть ли уже админ
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Создание администратора...")
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print(f"Администратор создан: admin / admin123")
        else:
            print("Администратор уже существует")
        
        # Проверяем базовые ингредиенты
        base_count = Ingredient.query.filter_by(is_public=True).count()
        if base_count == 0 and admin:
            print("Создание базовых ингредиентов...")
            base_ingredients = [
                Ingredient(
                    name='Куриная грудка',
                    calories=165,
                    proteins=31,
                    fats=3.6,
                    carbs=0,
                    is_public=True,
                    user_id=admin.id
                ),
                Ingredient(
                    name='Рис варёный',
                    calories=130,
                    proteins=2.7,
                    fats=0.3,
                    carbs=28,
                    is_public=True,
                    user_id=admin.id
                ),
                Ingredient(
                    name='Яйцо куриное',
                    calories=155,
                    proteins=13,
                    fats=11,
                    carbs=1.1,
                    is_public=True,
                    user_id=admin.id
                ),
                Ingredient(
                    name='Брокколи',
                    calories=34,
                    proteins=2.8,
                    fats=0.4,
                    carbs=6.6,
                    is_public=True,
                    user_id=admin.id
                ),
                Ingredient(
                    name='Творог 5%',
                    calories=121,
                    proteins=17,
                    fats=5,
                    carbs=1.8,
                    is_public=True,
                    user_id=admin.id
                ),
                Ingredient(
                    name='Овсянка',
                    calories=389,
                    proteins=16.9,
                    fats=6.9,
                    carbs=66.3,
                    is_public=True,
                    user_id=admin.id
                ),
                Ingredient(
                    name='Бананы',
                    calories=89,
                    proteins=1.1,
                    fats=0.3,
                    carbs=22.8,
                    is_public=True,
                    user_id=admin.id
                ),
                Ingredient(
                    name='Молоко 2.5%',
                    calories=52,
                    proteins=2.9,
                    fats=2.5,
                    carbs=4.7,
                    is_public=True,
                    user_id=admin.id
                ),
            ]
            
            db.session.add_all(base_ingredients)
            db.session.commit()
            print(f"Создано {len(base_ingredients)} базовых ингредиентов")
        else:
            print(f"Найдено {base_count} общедоступных ингредиентов")
        
        print("База данных готова к работе!")
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Инициализация базы данных Nutrition Calculator')
    parser.add_argument('--drop', action='store_true', help='Удалить все таблицы перед созданием')
    
    args = parser.parse_args()
    
    try:
        init_database(args.drop)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)