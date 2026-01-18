from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_, text
from app import db
from app.models import Ingredient, Recipe, recipe_ingredients
from app.forms import IngredientForm, RecipeForm, CalculationForm
from app.calculation import calculate_optimal_diet, find_best_recipes

bp = Blueprint('user', __name__)

@bp.route('/ingredients', methods=['GET'])
@login_required
def api_ingredients():
    """API для получения списка ингредиентов (для выпадающих списков)"""
    ingredients = Ingredient.query.filter(
        or_(
            Ingredient.user_id == current_user.id,
            Ingredient.is_public == True
        )
    ).order_by(Ingredient.name).all()

    return jsonify([
        {
            'id': ing.id,
            'name': ing.name,
            'calories': ing.calories,
            'proteins': ing.proteins,
            'fats': ing.fats,
            'carbs': ing.carbs
        }
        for ing in ingredients
    ])

@bp.route('/ingredients', methods=['POST'])
@login_required
def api_add_ingredient():
    """API для добавления ингредиента через AJAX"""
    try:
        data = request.get_json()

        # Валидация
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Название ингредиента обязательно'})

        # Проверяем, не существует ли уже такой ингредиент
        existing = Ingredient.query.filter(
            Ingredient.name.ilike(data['name']),
            Ingredient.user_id == current_user.id
        ).first()

        if existing:
            return jsonify({'success': False, 'message': 'У вас уже есть ингредиент с таким названием'})

        # Создаем ингредиент
        ingredient = Ingredient(
            name=data['name'].strip(),
            calories=float(data['calories']),
            proteins=float(data['proteins']),
            fats=float(data['fats']),
            carbs=float(data['carbs']),
            user_id=current_user.id,
            is_public=data.get('is_public', False) and current_user.is_admin
        )

        db.session.add(ingredient)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Ингредиент успешно добавлен!',
            'ingredient_id': ingredient.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

@bp.route('/recipes', methods=['POST'])
@login_required
def api_add_recipe():
    """API для добавления рецепта через AJAX"""
    try:
        print("=== API_ADD_RECIPE CALLED ===")

        if not request.is_json:
            return jsonify({'success': False, 'message': 'Требуется JSON'}), 400

        data = request.get_json()
        print(f"Received data: {data}")

        # Валидация
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Название рецепта обязательно'}), 400

        if not data.get('instructions'):
            return jsonify({'success': False, 'message': 'Инструкции приготовления обязательны'}), 400

        if not data.get('ingredients') or len(data['ingredients']) == 0:
            return jsonify({'success': False, 'message': 'Добавьте хотя бы один ингредиент'}), 400

        # Создаем рецепт
        recipe = Recipe(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            instructions=data['instructions'].strip(),
            image_url=data.get('image_url', '').strip() or None,
            user_id=current_user.id,
            is_public=False
        )

        db.session.add(recipe)
        db.session.flush()  # Получаем ID рецепта
        print(f"Recipe created with ID: {recipe.id}")

        # Добавляем ингредиенты через ассоциативную таблицу
        ingredients_added = 0
        for i, ing_data in enumerate(data['ingredients']):
            try:
                ingredient_id = int(ing_data.get('ingredient_id', 0))
                amount_grams = float(ing_data.get('amount', 0))

                if ingredient_id <= 0 or amount_grams <= 0:
                    print(f"Skipping ingredient {i+1}: invalid values")
                    continue

                # Проверяем существование ингредиента
                ingredient = Ingredient.query.get(ingredient_id)
                if not ingredient:
                    print(f"Error: Ingredient {ingredient_id} not found")
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'message': f'Ингредиент с ID {ingredient_id} не найден'
                    }), 400

                # ВСТАВКА В АССОЦИАТИВНУЮ ТАБЛИЦУ
                # Способ 1: Используем SQLAlchemy insert
                from sqlalchemy import insert

                stmt = insert(recipe_ingredients).values(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient_id,
                    amount_grams=amount_grams
                )
                db.session.execute(stmt)

                ingredients_added += 1
                print(f"Added ingredient {ingredient_id} with amount {amount_grams}")

            except (ValueError, TypeError) as e:
                print(f"Error processing ingredient {i+1}: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Неверный формат данных ингредиента: {str(e)}'
                }), 400

        if ingredients_added == 0:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Не добавлено ни одного валидного ингредиента'
            }), 400

        print(f"Added {ingredients_added} ingredients to association table")
        db.session.commit()
        print("Recipe saved successfully!")

        return jsonify({
            'success': True,
            'message': 'Рецепт успешно добавлен',
            'recipe_id': recipe.id
        })

    except Exception as e:
        print(f"EXCEPTION in api_add_recipe: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

#ENDPOINTS ДЛЯ УДАЛЕНИЯ:

@bp.route('/my-ingredients/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_ingredient(id):
    """API для удаления ингредиента через AJAX"""
    ingredient = Ingredient.query.get_or_404(id)

    # Проверяем права
    if ingredient.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Нет прав для удаления'}), 403

    # Проверяем, используется ли ингредиент в рецептах

    result = db.session.execute(
        text("SELECT COUNT(*) FROM recipe_ingredients WHERE ingredient_id = :ingredient_id"),
        {'ingredient_id': id}
    ).fetchone()

    usage_count = result[0] if result else 0

    if usage_count > 0:
        # Получаем список рецептов, где используется ингредиент
        recipes_result = db.session.execute(
            text("""
                SELECT r.id, r.name
                FROM recipes r
                JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                WHERE ri.ingredient_id = :ingredient_id
                LIMIT 5
            """),
            {'ingredient_id': id}
        ).fetchall()

        recipe_names = [r[1] for r in recipes_result]

        return jsonify({
            'success': False,
            'message': f'Невозможно удалить ингредиент, так как он используется в {usage_count} рецептах',
            'used_in_recipes': recipe_names,
            'usage_count': usage_count
        })

    try:
        db.session.delete(ingredient)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Ингредиент удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при удалении: {str(e)}'})

@bp.route('/my-recipes/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_recipe(id):
    """API для удаления рецепта через AJAX"""
    recipe = Recipe.query.get_or_404(id)

    # Проверяем права
    if recipe.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Нет прав для удаления'}), 403

    try:
        print(f"=== DELETING RECIPE {id} ===")

        # 1. Сначала удаляем связи из ассоциативной таблицы

        # Проверяем, есть ли связи
        result = db.session.execute(
            text("SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = :recipe_id"),
            {'recipe_id': id}
        ).fetchone()

        link_count = result[0] if result else 0
        print(f"Found {link_count} ingredient links to delete")

        # Удаляем связи
        if link_count > 0:
            db.session.execute(
                text("DELETE FROM recipe_ingredients WHERE recipe_id = :recipe_id"),
                {'recipe_id': id}
            )
            print(f"Deleted {link_count} links from recipe_ingredients")

        # 2. Затем удаляем сам рецепт
        db.session.delete(recipe)

        # 3. Коммитим изменения
        db.session.commit()

        print(f"Recipe {id} deleted successfully")

        return jsonify({
            'success': True,
            'message': 'Рецепт удален',
            'deleted_links': link_count
        })

    except Exception as e:
        print(f"Error deleting recipe {id}: {str(e)}")
        import traceback
        traceback.print_exc()

        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении: {str(e)}'
        }), 500


#РАССЧЕТ

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
    selected_ingredients_data = []

    if form.validate_on_submit():
        targets = {
            'calories': form.target_calories.data,
            'proteins': form.target_proteins.data,
            'fats': form.target_fats.data,
            'carbs': form.target_carbs.data
        }

        # Получаем выбранные пользователем ингредиенты

        selected_ingredients = []
        selected_amounts = []

        # Собираем все поля ingredient_id_*
        for key, value in request.form.items():
            if key.startswith('ingredient_id_'):
                ingredient_id = int(value)

                # Получаем количество из поля amount_<id>
                amount_key = f'amount_{ingredient_id}'
                amount = request.form.get(amount_key, 100)

                # Находим ингредиент
                ingredient = Ingredient.query.get(ingredient_id)
                if ingredient:
                    selected_ingredients.append(ingredient)
                    selected_amounts.append(float(amount))
                    selected_ingredients_data.append({
                        'id': ingredient.id,
                        'name': ingredient.name,
                        'amount': float(amount),
                        'calories': ingredient.calories,
                        'proteins': ingredient.proteins,
                        'fats': ingredient.fats,
                        'carbs': ingredient.carbs
                    })

        if not selected_ingredients:
            flash('Выберите хотя бы один ингредиент', 'error')
        else:
            # Рассчитываем оптимальную диету с выбранными ингредиентами
            result = calculate_optimal_diet(selected_ingredients, targets, selected_amounts)

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
                         ingredients=available_ingredients,
                         selected_ingredients=selected_ingredients_data)


@bp.route('/my-ingredients', methods=['GET', 'POST'])
@login_required
def my_ingredients():
    # Обработка добавления нового ингредиента
    if request.method == 'POST' and request.content_type == 'application/x-www-form-urlencoded':
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

    if current_user.is_admin:
        query = Ingredient.query.filter(
            (Ingredient.user_id == current_user.id) |
            (Ingredient.is_public == True)
        )
    else:
        query = Ingredient.query.filter(
            (Ingredient.user_id == current_user.id)
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

@bp.route('/ingredient/<int:ingredient_id>/details', methods=['GET'])
@login_required
def get_ingredient_details(ingredient_id):
    """Получить детали ингредиента"""
    ingredient = Ingredient.query.get_or_404(ingredient_id)

    # Проверяем права
    if ingredient.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Нет прав'}), 403

    return jsonify({
        'success': True,
        'ingredient': {
            'id': ingredient.id,
            'name': ingredient.name,
            'calories': ingredient.calories,
            'proteins': ingredient.proteins,
            'fats': ingredient.fats,
            'carbs': ingredient.carbs
        }
    })

@bp.route('/ingredient/<int:ingredient_id>/update', methods=['PUT'])
@login_required
def update_ingredient(ingredient_id):
    """Обновить ингредиент"""
    ingredient = Ingredient.query.get_or_404(ingredient_id)

    # Проверяем права
    if ingredient.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Нет прав'}), 403

    try:
        data = request.get_json()

        # Обновляем
        ingredient.name = data['name'].strip()
        ingredient.calories = float(data['calories'])
        ingredient.proteins = float(data['proteins'])
        ingredient.fats = float(data['fats'])
        ingredient.carbs = float(data['carbs'])

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Ингредиент обновлен!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500


@bp.route('/my-recipes', methods=['GET', 'POST'])
@login_required
def my_recipes():
    # Обработка добавления нового рецепта
    if request.method == 'POST' and request.content_type == 'application/x-www-form-urlencoded':
        form = RecipeForm()

        # Динамическое добавление полей ингредиентов
        class DynamicRecipeForm(RecipeForm):
            pass

        for i in range(len(request.form.getlist('ingredient_id'))):
            setattr(DynamicRecipeForm, f'ingredient_id_{i}', None)
            setattr(DynamicRecipeForm, f'ingredient_amount_{i}', None)

        form = DynamicRecipeForm()

        if form.validate():
            recipe = Recipe(
                name=form.name.data,
                description=form.description.data,
                instructions=form.instructions.data,
                image_url=form.image_url.data,
                is_public=form.is_public.data and current_user.is_admin,
                user_id=current_user.id
            )

            db.session.add(recipe)
            db.session.flush()

            # Добавляем ингредиенты
            ingredient_ids = request.form.getlist('ingredient_id')
            amounts = request.form.getlist('ingredient_amount')

            for ing_id, amount in zip(ingredient_ids, amounts):
                if ing_id and amount:
                    recipe_ingredient = recipe_ingredients(
                        recipe_id=recipe.id,
                        ingredient_id=int(ing_id),
                        amount=float(amount)
                    )
                    db.session.add(recipe_ingredient)

            db.session.commit()
            flash('Рецепт успешно добавлен!', 'success')
            return redirect(url_for('user.my_recipes'))

    # Получение и фильтрация рецептов
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search = request.args.get('search', '').strip()

    query = Recipe.query.filter(
        or_(
            Recipe.user_id == current_user.id,
            Recipe.is_public == True
        )
    )

    if search:
        query = query.filter(Recipe.name.ilike(f'%{search}%'))

    recipes = query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Получаем доступные ингредиенты для формы
    available_ingredients = Ingredient.query.filter(
        or_(
            Ingredient.user_id == current_user.id,
            Ingredient.is_public == True
        )
    ).order_by(Ingredient.name).all()

    form = RecipeForm()

    return render_template('user/my_recipes.html',
                         recipes=recipes,
                         form=form,
                         search=search,
                         ingredients=available_ingredients)

@bp.route('/my-recipes/<int:recipe_id>/details', methods=['GET'])
@login_required
def get_recipe_details(recipe_id):
    """Получить детали рецепта"""
    recipe = Recipe.query.get_or_404(recipe_id)

    # Проверяем права
    if recipe.user_id != current_user.id and not recipe.is_public:
        return jsonify({'success': False, 'message': 'Нет прав для просмотра'}), 403

    # Получаем ингредиенты
    ingredients_result = db.session.execute(
        text("""
            SELECT i.id, i.name, i.calories, ri.amount_grams
            FROM recipe_ingredients ri
            JOIN ingredient i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = :recipe_id
        """),
        {'recipe_id': recipe_id}
    ).fetchall()

    # Формируем список ингредиентов
    ingredients = []
    for row in ingredients_result:
        ingredients.append({
            'id': row[0],
            'name': row[1],
            'calories_per_100g': float(row[2]),
            'amount_grams': float(row[3])
        })

    # Рассчитываем КБЖУ
    nutrition = recipe.calculate_nutrition()

    return jsonify({
        'success': True,
        'recipe': {
            'id': recipe.id,
            'name': recipe.name,
            'description': recipe.description or '',
            'instructions': recipe.instructions,
            'image_url': recipe.image_url,
            'is_public': recipe.is_public,
            'user_id': recipe.user_id
        },
        'ingredients': ingredients,
        'nutrition': {
            'calories': nutrition['calories'],
            'proteins': nutrition['proteins'],
            'fats': nutrition['fats'],
            'carbs': nutrition['carbs']
        }
    })

@bp.route('/my-recipes/<int:recipe_id>/update', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Обновить рецепт"""
    recipe = Recipe.query.get_or_404(recipe_id)

    # Проверяем права
    if recipe.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Нет прав для редактирования'}), 403

    try:
        data = request.get_json()

        # Валидация
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Название рецепта обязательно'}), 400

        if not data.get('instructions'):
            return jsonify({'success': False, 'message': 'Инструкции приготовления обязательны'}), 400

        if not data.get('ingredients') or len(data['ingredients']) == 0:
            return jsonify({'success': False, 'message': 'Добавьте хотя бы один ингредиент'}), 400

        # Обновляем рецепт
        recipe.name = data['name'].strip()
        recipe.description = data.get('description', '').strip()
        recipe.instructions = data['instructions'].strip()
        recipe.image_url = data.get('image_url', '').strip() or None

        if current_user.is_admin:
            recipe.is_public = data.get('is_public', False)

        # Удаляем старые ингредиенты
        db.session.execute(
            text("DELETE FROM recipe_ingredients WHERE recipe_id = :recipe_id"),
            {'recipe_id': recipe_id}
        )

        # Добавляем новые ингредиенты
        for ing_data in data['ingredients']:
            ingredient_id = int(ing_data.get('ingredient_id', 0))
            amount_grams = float(ing_data.get('amount', 0))

            if ingredient_id <= 0 or amount_grams <= 0:
                continue

            # Проверяем существование ингредиента
            ingredient = Ingredient.query.get(ingredient_id)
            if not ingredient:
                continue

            # Добавляем связь
            db.session.execute(
                text("""
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount_grams)
                    VALUES (:recipe_id, :ingredient_id, :amount_grams)
                """),
                {
                    'recipe_id': recipe_id,
                    'ingredient_id': ingredient_id,
                    'amount_grams': amount_grams
                }
            )

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Рецепт успешно обновлен!'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating recipe: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500