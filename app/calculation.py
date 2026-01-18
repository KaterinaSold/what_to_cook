import numpy as np
from scipy.optimize import minimize

def calculate_optimal_diet(available_ingredients, targets, initial_amounts=None):
    """
    Рассчитать оптимальные количества ингредиентов для достижения целевых КБЖУ

    Args:
        available_ingredients: список объектов Ingredient
        targets: словарь с ключами 'calories', 'proteins', 'fats', 'carbs'
        initial_amounts: начальные количества (если None, то не учитывается)

    Returns:
        Словарь с оптимальными количествами ингредиентов
    """

    if not available_ingredients:
        return {
            'success': False,
            'error': 'Нет доступных ингредиентов'
        }

    # Преобразуем данные в массивы NumPy
    n_ingredients = len(available_ingredients)

    # Матрица питательных веществ (каждый столбец - ингредиент)
    nutrients = np.zeros((4, n_ingredients))
    for i, ing in enumerate(available_ingredients):
        nutrients[0, i] = ing.calories  # калории на 100г
        nutrients[1, i] = ing.proteins  # белки на 100г
        nutrients[2, i] = ing.fats      # жиры на 100г
        nutrients[3, i] = ing.carbs     # углеводы на 100г

    # Целевые значения
    target_vector = np.array([
        targets['calories'],
        targets['proteins'],
        targets['fats'],
        targets['carbs']
    ])

    def objective(x):
        """Целевая функция - минимизация отклонения от целевых значений"""
        # x - вектор весов (сколько грамм каждого ингредиента)
        # Насчитываем фактические КБЖУ
        actual = nutrients @ (x / 100.0)  # делим на 100, т.к. КБЖУ на 100г

        # Квадратичная ошибка
        error = np.sum((actual - target_vector) ** 2)

        # Штраф за отрицательные значения
        penalty = 1000 * np.sum(np.maximum(-x, 0) ** 2)

        # Штраф за слишком большие значения (больше 1000г)
        large_penalty = 0.01 * np.sum(np.maximum(x - 1000, 0) ** 2)

        # Если есть начальные количества, штрафуем за сильное отклонение
        if initial_amounts is not None:
            for i in range(n_ingredients):
                if initial_amounts[i] > 0:
                    # Штраф за изменение больше чем в 2 раза
                    if x[i] > initial_amounts[i] * 2 or x[i] < initial_amounts[i] * 0.5:
                        error += 100 * ((x[i] - initial_amounts[i]) ** 2)

        return error + penalty + large_penalty

    # Начальное приближение (равные доли, сумма = 500г)
    if initial_amounts is not None and len(initial_amounts) == n_ingredients:
        # Используем указанные пользователем количества как начальное приближение
        x0 = np.array(initial_amounts, dtype=float)
    else:
        # Равные доли, сумма = 500г
        x0 = np.ones(n_ingredients) * (500 / max(n_ingredients, 1))

    # Границы (0-1000г для каждого ингредиента)
    bounds = [(0, 1000) for _ in range(n_ingredients)]

    # Ограничения
    constraints = [
        {'type': 'ineq', 'fun': lambda x: np.sum(x) - 200},   # минимум 200г
        {'type': 'ineq', 'fun': lambda x: 5000 - np.sum(x)},  # максимум 5000г
    ]

    # Оптимизация
    result = minimize(
        objective,
        x0,
        bounds=bounds,
        constraints=constraints,
        method='SLSQP',
        options={'maxiter': 1000, 'ftol': 1e-6}
    )

    if result.success:
        # Округляем до 5 грамм и фильтруем маленькие значения
        optimal_weights = np.round(result.x / 5) * 5

        # Собираем результат
        result_dict = {}
        total_weight = 0

        for i, ing in enumerate(available_ingredients):
            weight = float(optimal_weights[i])
            if weight >= 5:  # включаем только если больше или равно 5г
                result_dict[ing.id] = {
                    'ingredient': ing,
                    'grams': weight,
                    'nutrition': {
                        'calories': ing.calories * weight / 100,
                        'proteins': ing.proteins * weight / 100,
                        'fats': ing.fats * weight / 100,
                        'carbs': ing.carbs * weight / 100
                    }
                }
                total_weight += weight

        if not result_dict:
            return {
                'success': False,
                'error': 'Не удалось найти подходящие количества ингредиентов'
            }

        # Рассчитываем итоговые КБЖУ
        total_nutrition = {
            'calories': 0,
            'proteins': 0,
            'fats': 0,
            'carbs': 0
        }

        for ing_data in result_dict.values():
            for key in total_nutrition:
                total_nutrition[key] += ing_data['nutrition'][key]

        # Рассчитываем отклонения
        deviations = {}
        for key in total_nutrition:
            if targets[key] > 0:
                deviations[key] = round((total_nutrition[key] - targets[key])
                                        / targets[key] * 100, 1)
            else:
                deviations[key] = 0

        return {
            'ingredients': result_dict,
            'total_nutrition': {k: round(v, 1) for k, v in total_nutrition.items()},
            'target_nutrition': targets,
            'deviations': deviations,
            'total_weight': round(total_weight, 1),
            'success': True
        }
    else:
        return {
            'success': False,
            'error': f'Ошибка оптимизации: {result.message}'
        }

def find_best_recipes(optimal_ingredients, available_recipes, top_n=3):
    """
    Найти лучшие рецепты на основе оптимальных ингредиентов

    Args:
        optimal_ingredients: результат calculate_optimal_diet['ingredients']
        available_recipes: список доступных рецептов
        top_n: сколько рецептов вернуть

    Returns:
        Список рецептов с оценкой соответствия
    """
    if not optimal_ingredients or not available_recipes:
        return []

    # ID оптимальных ингредиентов
    optimal_ingredient_ids = set(optimal_ingredients.keys())
    optimal_ingredient_weights = {id: data['grams'] for id, data in optimal_ingredients.items()}

    scored_recipes = []

    for recipe in available_recipes:
        # Получаем ID ингредиентов рецепта
        recipe_ingredient_ids = {ing.id for ing in recipe.ingredients}

        if not recipe_ingredient_ids:
            continue

        # 1. Количество совпадающих ингредиентов
        matching_ingredients = optimal_ingredient_ids.intersection(recipe_ingredient_ids)
        matching_count = len(matching_ingredients)

        # 2. Процент совпадения по ингредиентам
        match_percentage = matching_count / len(recipe_ingredient_ids) * 100

        # 3. Суммарный вес совпадающих ингредиентов
        total_matching_weight = 0
        for ing_id in matching_ingredients:
            total_matching_weight += optimal_ingredient_weights.get(ing_id, 0)

        # 4. Общий вес рецепта
        recipe_weight = 0
        for ingredient in recipe.ingredients:
            amount = recipe.get_ingredient_amount(ingredient.id)
            if amount:
                recipe_weight += amount

        if recipe_weight == 0:
            continue

        # 5. Процент покрытия по весу
        weight_coverage = min(total_matching_weight / recipe_weight * 100, 100)

        # Итоговая оценка (можно настроить коэффициенты)
        score = (
            match_percentage * 0.4 +          # 40% за совпадение ингредиентов
            weight_coverage * 0.4 +           # 40% за покрытие веса
            (matching_count * 10) * 0.2       # 20% за количество совпадений
        )

        # Рассчитываем КБЖУ рецепта
        recipe_nutrition = recipe.calculate_nutrition()

        scored_recipes.append({
            'recipe': recipe,
            'score': round(score, 2),
            'matching_count': matching_count,
            'match_percentage': round(match_percentage, 1),
            'weight_coverage': round(weight_coverage, 1),
            'recipe_weight': round(recipe_weight, 1),
            'nutrition': recipe_nutrition
        })

    # Сортируем по убыванию оценки
    scored_recipes.sort(key=lambda x: x['score'], reverse=True)

    return scored_recipes[:top_n]
