from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import Ingredient, Recipe, recipe_ingredients
from app.forms import IngredientForm, RecipeForm, CalculationForm, RecipeIngredientForm
from app.calculation import calculate_optimal_diet, find_best_recipes
from wtforms import FieldList, FormField
bp = Blueprint('user', __name__)

@bp.route('/calculate', methods=['GET', 'POST'])
@login_required
def calculate():
    form = CalculationForm()
    
    # Получаем доступные ингредиенты
    available_ingredients = Ingredient.query.filter(
        or_(
            Ingredient.user_id == current_user.id,
            Ingredient.is_public == True
        )
    ).order_by(Ingredient.name).all()
    
    result = None
    best_recipes = []
    
    if form.validate_on_submit():
        targets = {
            'calories': form.target_calories.data,
            'proteins': form.target_proteins.data,
            'fats': form.target_fats.data,
            'carbs': form.target_carbs.data
        }
        
        # Рассчитываем оптимальную диету
        result = calculate_optimal_diet(available_ingredients, targets)
        
        if result['success']:
            # Ищем подходящие рецепты
            available_recipes = Recipe.query.filter(
                or_(
                    Recipe.user_id == current_user.id,
                    Recipe.is_public == True
                )
            ).all()
            
            best_recipes = find_best_recipes(
                result['ingredients'],
                available_recipes
            )
            
            flash('Расчёт выполнен успешно!', 'success')
        else:
            flash(f'Ошибка: {result.get("error", "Неизвестная ошибка")}', 'danger')
    
    return render_template('user/calculate.html',
                         form=form,
                         result=result,
                         best_recipes=best_recipes,
                         ingredients=available_ingredients)

@bp.route('/my-ingredients', methods=['GET', 'POST'])
@login_required
def my_ingredients():
    # Обработка добавления нового ингредиента
    if request.method == 'POST':
        form = IngredientForm()
        if form.validate():
            ingredient = Ingredient(
                name=form.name.data,
                calories=form.calories.data,
                proteins=form.proteins.data,
                fats=form.fats.data,
                carbs=form.carbs.data,
                is_public=form.is_public.data and current_user.is_admin,
                user_id=current_user.id
            )
            
            db.session.add(ingredient)
            db.session.commit()
            flash('Ингредиент успешно добавлен!', 'success')
            return redirect(url_for('user.my_ingredients'))
    
    # Получение и фильтрация ингредиентов
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Ingredient.query.filter(
        or_(
            Ingredient.user_id == current_user.id,
            Ingredient.is_public == True
        )
    )
    
    # Поиск
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Ingredient.name.ilike(f'%{search}%'))
    
    # Сортировка
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    sort_mapping = {
        'calories': Ingredient.calories,
        'proteins': Ingredient.proteins,
        'fats': Ingredient.fats,
        'carbs': Ingredient.carbs
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
    
    return render_template('user/my_ingredients.html',
                         ingredients=ingredients,
                         form=form,
                         search=search,
                         sort_by=sort_by,
                         sort_order=sort_order)

@bp.route('/my-recipes', methods=['GET', 'POST'])
@login_required
def my_recipes():
    # Получаем доступные ингредиенты для выпадающего списка
    available_ingredients = Ingredient.query.filter(
        or_(
            Ingredient.user_id == current_user.id,
            Ingredient.is_public == True
        )
    ).order_by(Ingredient.name).all()
    
    # Создаём форму с динамическим выбором ингредиентов
    class DynamicRecipeForm(RecipeForm):
        pass
    
    # Динамически добавляем поля для ингредиентов
    DynamicRecipeForm.ingredients = FieldList(FormField(RecipeIngredientForm), min_entries=1)
    
    form = DynamicRecipeForm()
    
    # Заполняем выбор существующих ингредиентов
    for subform in form.ingredients:
        subform.existing_ingredient.choices = [(0, '-- Выберите ингредиент --')] + \
                                             [(ing.id, ing.name) for ing in available_ingredients]
    
    if request.method == 'POST' and form.validate():
        # Создаём рецепт
        recipe = Recipe(
            name=form.name.data,
            description=form.description.data,
            instructions=form.instructions.data,
            image_url=form.image_url.data,
            is_public=form.is_public.data and current_user.is_admin,
            user_id=current_user.id
        )
        
        db.session.add(recipe)
        db.session.flush()  # Получаем ID рецепта
        
        # Обрабатываем ингредиенты
        for ingredient_form in form.ingredients:
            ingredient_id = None
            
            # Если выбран существующий ингредиент
            if ingredient_form.existing_ingredient.data and ingredient_form.existing_ingredient.data != 0:
                ingredient_id = ingredient_form.existing_ingredient.data
            
            # Если создаётся новый ингредиент
            elif ingredient_form.new_ingredient_name.data:
                # Проверяем, не существует ли уже такой ингредиент
                existing = Ingredient.query.filter_by(
                    name=ingredient_form.new_ingredient_name.data,
                    user_id=current_user.id
                ).first()
                
                if existing:
                    ingredient_id = existing.id
                else:
                    # Создаём новый ингредиент
                    new_ingredient = Ingredient(
                        name=ingredient_form.new_ingredient_name.data,
                        calories=ingredient_form.calories.data or 0,
                        proteins=ingredient_form.proteins.data or 0,
                        fats=ingredient_form.fats.data or 0,
                        carbs=ingredient_form.carbs.data or 0,
                        is_public=False,
                        user_id=current_user.id
                    )
                    db.session.add(new_ingredient)
                    db.session.flush()
                    ingredient_id = new_ingredient.id
            
            # Добавляем ингредиент в рецепт
            if ingredient_id and ingredient_form.amount.data:
                # Добавляем связь в промежуточную таблицу
                stmt = recipe_ingredients.insert().values(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient_id,
                    amount_grams=ingredient_form.amount.data
                )
                db.session.execute(stmt)
        
        db.session.commit()
        flash('Рецепт успешно добавлен!', 'success')
        return redirect(url_for('user.my_recipes'))
    
    # Для GET запроса
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Recipe.query.filter(
        or_(
            Recipe.user_id == current_user.id,
            Recipe.is_public == True
        )
    )
    
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Recipe.name.ilike(f'%{search}%'))
    
    recipes = query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('user/my_recipes.html',
                         recipes=recipes,
                         form=form,
                         search=search,
                         ingredients=available_ingredients)


@bp.route('/api/ingredient/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    
    # Проверяем права
    if ingredient.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Нет прав для удаления'}), 403
    
    db.session.delete(ingredient)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/api/recipe/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    
    # Проверяем права
    if recipe.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Нет прав для удаления'}), 403
    
    db.session.delete(recipe)
    db.session.commit()
    
    return jsonify({'success': True})