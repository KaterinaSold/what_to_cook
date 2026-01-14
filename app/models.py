from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Промежуточная таблица для связи многие-ко-многим
recipe_ingredients = db.Table('recipe_ingredients',
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id', ondelete='CASCADE'), primary_key=True),
    db.Column('ingredient_id', db.Integer, db.ForeignKey('ingredient.id', ondelete='CASCADE'), primary_key=True),
    db.Column('amount_grams', db.Integer, nullable=False, default=100)
)

class User(UserMixin, db.Model):
    tablename = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    ingredients = db.relationship('Ingredient', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    recipes = db.relationship('Recipe', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def repr(self):
        return f'<User {self.username}>'

class Ingredient(db.Model):
    tablename = 'ingredient'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Float, nullable=False)  # на 100г
    proteins = db.Column(db.Float, nullable=False)  # на 100г
    fats = db.Column(db.Float, nullable=False)      # на 100г
    carbs = db.Column(db.Float, nullable=False)     # на 100г
    is_public = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с рецептами
    recipes = db.relationship('Recipe', secondary=recipe_ingredients, back_populates='ingredients')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'calories': self.calories,
            'proteins': self.proteins,
            'fats': self.fats,
            'carbs': self.carbs,
            'is_public': self.is_public,
            'user_id': self.user_id
        }
    
    def repr(self):
        return f'<Ingredient {self.name}>'

class Recipe(db.Model):
    tablename = 'recipe'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    is_public = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с ингредиентами
    ingredients = db.relationship('Ingredient', secondary=recipe_ingredients, back_populates='recipes')
    
    def get_ingredient_amount(self, ingredient_id):
        """Получить количество ингредиента в рецепте"""
        from sqlalchemy import select
        
        stmt = select(recipe_ingredients.c.amount_grams).where(
            recipe_ingredients.c.recipe_id == self.id,
            recipe_ingredients.c.ingredient_id == ingredient_id
        )
        result = db.session.execute(stmt).fetchone()
        return result[0] if result else 0
    
    def calculate_nutrition(self):
        """Рассчитать КБЖУ для всего рецепта"""
        total_calories = 0
        total_proteins = 0
        total_fats = 0
        total_carbs = 0
        
        for ingredient in self.ingredients:
            amount = self.get_ingredient_amount(ingredient.id)
            if amount:
                # Пересчитываем КБЖУ на фактическое количество
                total_calories += (ingredient.calories * amount / 100)
                total_proteins += (ingredient.proteins * amount / 100)
                total_fats += (ingredient.fats * amount / 100)
                total_carbs += (ingredient.carbs * amount / 100)
        
        return {
            'calories': round(total_calories, 1),
            'proteins': round(total_proteins, 1),
            'fats': round(total_fats, 1),
            'carbs': round(total_carbs, 1)
        }
    
    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'instructions': self.instructions,
            'image_url': self.image_url,
            'is_public': self.is_public,
            'user_id': self.user_id,
            'nutrition': self.calculate_nutrition(),
            'ingredients': []
        }
        
        for ingredient in self.ingredients:
            amount = self.get_ingredient_amount(ingredient.id)
            if amount:
                data['ingredients'].append({
                    **ingredient.to_dict(),
                    'amount_grams': amount
                })
        
        return data
    
    def repr(self):
        return f'<Recipe {self.name}>'