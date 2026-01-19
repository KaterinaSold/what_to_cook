def test_calculate_optimal_diet_basic():
    """Базовый тест функции расчёта"""
    print("\nТестирование функции calculate_optimal_diet...")

    try:
        from app.calculation import calculate_optimal_diet

        class SimpleIngredient:
            def init(self, id, name, calories, proteins, fats, carbs):
                self.id = id
                self.name = name
                self.calories = calories
                self.proteins = proteins
                self.fats = fats
                self.carbs = carbs

        ingredients = [
            SimpleIngredient(1, "Белок", 100, 25, 1, 0),
            SimpleIngredient(2, "Углеводы", 100, 2, 0, 25)
        ]

        targets = {
            'calories': 500,
            'proteins': 50,
            'fats': 10,
            'carbs': 50
        }

        result = calculate_optimal_diet(ingredients, targets)

        assert isinstance(result, dict)
        assert 'success' in result

        if result['success']:
            assert 'ingredients' in result
            assert 'total_nutrition' in result
            print("[OK] Функция расчёта возвращает корректную структуру при успехе")
        else:
            assert 'error' in result
            print("[OK] Функция расчёта возвращает корректную структуру при ошибке")

        return True

    except Exception as e:
        print(f"[ERROR] Ошибка функции расчёта: {e}")
        return False

def test_calculate_edge_cases():
    """Тест граничных случаев расчёта"""
    print("\nТестирование граничных случаев...")

    try:
        from app.calculation import calculate_optimal_diet

        result1 = calculate_optimal_diet([], {'calories': 1000})
        assert result1['success'] == False
        assert 'ингредиент' in result1.get('error', '').lower()
        print("[OK] Обработка пустых ингредиентов")

        class SimpleIngredient:
            def init(self):
                self.id = 1
                self.name = "test"
                self.calories = 100
                self.proteins = 10
                self.fats = 5
                self.carbs = 2

        result2 = calculate_optimal_diet([SimpleIngredient()], {
            'calories': 0,
            'proteins': 0,
            'fats': 0,
            'carbs': 0
        })

        assert isinstance(result2, dict)
        print("[OK] Обработка нулевых целей")

        return True

    except Exception as e:
        print(f"[ERROR] Ошибка граничных случаев: {e}")
        return False

def test_find_best_recipes_simple():
    """Простой тест поиска рецептов"""
    print("\nТестирование функции find_best_recipes...")

    try:
        from app.calculation import find_best_recipes

        result1 = find_best_recipes({}, [])
        assert result1 == []
        print("[OK] Обработка пустых данных")

        class MockIngredient:
            def init(self, id):
                self.id = id

        class MockRecipe:
            def init(self):
                self.id = 1
                self.name = "Тест"
                self.ingredients = []
                self.get_ingredient_amount = lambda x: 0
                self.calculate_nutrition = lambda: {'calories': 0, 'proteins': 0, 'fats': 0, 'carbs': 0}

        result2 = find_best_recipes(
            {1: {'ingredient': MockIngredient(1), 'grams': 100}},
            [MockRecipe()]
        )

        assert isinstance(result2, list)
        print("[OK] Обработка простых объектов")

        return True

    except Exception as e:
        print(f"[ERROR] Ошибка поиска рецептов: {e}")
        return False

def test_calculation_functions_exist():
    """Тест что функции существуют и вызываются"""
    print("\nПроверка существования функций...")

    try:
        from app.calculation import calculate_optimal_diet, find_best_recipes

        assert callable(calculate_optimal_diet)
        assert callable(find_best_recipes)

        import inspect
        sig1 = str(inspect.signature(calculate_optimal_diet))
        sig2 = str(inspect.signature(find_best_recipes))

        print(f"[OK] calculate_optimal_diet: {sig1}")
        print(f"[OK] find_best_recipes: {sig2}")

        return True

    except Exception as e:
        print(f"[ERROR] Ошибка проверки функций: {e}")
        return False

def run_all_calculation_tests():
    """Запуск всех тестов расчёта"""
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ ФУНКЦИЙ РАСЧЁТА")
    print("="*50)

    results = []
    results.append(test_calculate_optimal_diet_basic())
    results.append(test_calculate_edge_cases())
    results.append(test_find_best_recipes_simple())
    results.append(test_calculation_functions_exist())

    passed = sum([1 for r in results if r])
    total = len(results)

    print(f"\nИТОГО: {passed}/{total} тестов расчёта пройдено")

    if passed == total:
        print("Все тесты расчёта пройдены!")
        return True
    else:
        print("Есть проблемы с функциями расчёта")
        return False

if __name__ == "main":
    run_all_calculation_tests()