from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import Ingredient, Recipe, User
from app.forms import IngredientForm, RecipeForm

bp = Blueprint('admin', __name__)

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Требуются права администратора', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/ingredients')
@login_required
@admin_required
def ingredients():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    query = Ingredient.query
    
    # Поиск
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Ingredient.name.ilike(f'%{search}%'))
    
    # Фильтр по типу
    filter_type = request.args.get('filter', 'all')
    if filter_type == 'public':
        query = query.filter(Ingredient.is_public == True)
    elif filter_type == 'private':
        query = query.filter(Ingredient.is_public == False)
    
    # Сортировка
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    sort_mapping = {
        'calories': Ingredient.calories,
        'proteins': Ingredient.proteins,
        'fats': Ingredient.fats,
        'carbs': Ingredient.carbs,
        'created_at': Ingredient.created_at
    }
    
    if sort_by in sort_mapping:
        if sort_order == 'desc':
            query = query.order_by(sort_mapping[sort_by].desc())
        else:
            query = query.order_by(sort_mapping[sort_by])
    else:
        query = query.order_by(Ingredient.name)
    
    ingredients = query.paginate(page=page, per_page=per_page, error_out=False)
    
    form = IngredientForm()
    
    return render_template('admin/ingredients.html',
                         ingredients=ingredients,
                         form=form,
                         search=search,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         filter_type=filter_type)

@bp.route('/recipes')
@login_required
@admin_required
def recipes():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Recipe.query
    
    # Поиск
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Recipe.name.ilike(f'%{search}%'))
    
    # Фильтр по типу
    filter_type = request.args.get('filter', 'all')
    if filter_type == 'public':
        query = query.filter(Recipe.is_public == True)
    elif filter_type == 'private':
        query = query.filter(Recipe.is_public == False)
    
    recipes = query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    form = RecipeForm()
    
    return render_template('admin/recipes.html',
                         recipes=recipes,
                         form=form,
                         search=search,
                         filter_type=filter_type)

@bp.route('/api/ingredient/toggle-public/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_ingredient_public(id):
    ingredient = Ingredient.query.get_or_404(id)
    ingredient.is_public = not ingredient.is_public
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_public': ingredient.is_public
    })

@bp.route('/api/recipe/toggle-public/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_recipe_public(id):
    recipe = Recipe.query.get_or_404(id)
    recipe.is_public = not recipe.is_public
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_public': recipe.is_public
    })