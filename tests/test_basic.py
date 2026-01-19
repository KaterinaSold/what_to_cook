def test_import_flask():
    """Тест что Flask импортируется"""
    from flask import Flask
    app = Flask(__name__)
    assert app is not None
    print("[OK] Flask импортируется")
    return True

def test_import_models():
    """Тест что модели импортируются"""
    try:
        from app.models import User, Ingredient, Recipe
        print("[OK] Модели импортируются")
        return True
    except ImportError as e:
        print(f"[ERROR] Ошибка импорта моделей: {e}")
        return False

def test_create_simple_objects():
    """Тест создания простых объектов"""
    try:
        from app.models import User, Ingredient

        user = User(username="test", email="test@test.com")
        ingredient = Ingredient(name="test", calories=100, proteins=10, fats=5, carbs=2)

        assert user.username == "test"
        assert ingredient.name == "test"
        print("[OK] Объекты создаются")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка создания объектов: {e}")
        return False

def test_calculation_import():
    """Тест что функции расчёта импортируются"""
    try:
        from app.calculation import calculate_optimal_diet
        print("[OK] Функции расчёта импортируются")
        return True
    except ImportError as e:
        print(f"[ERROR] Ошибка импорта функций расчёта: {e}")
        return False

def run_all_basic_tests():
    """Запуск всех базовых тестов"""
    print("\n" + "="*50)
    print("ЗАПУСК БАЗОВЫХ ТЕСТОВ")
    print("="*50)

    results = []
    results.append(test_import_flask())
    results.append(test_import_models())
    results.append(test_create_simple_objects())
    results.append(test_calculation_import())

    passed = sum([1 for r in results if r])
    total = len(results)

    print(f"\nИТОГО: {passed}/{total} тестов пройдено")

    if passed == total:
        print("Все базовые тесты пройдены!")
        return True
    else:
        print("Есть проблемы с базовой функциональностью")
        return False

if __name__ == "main":
    run_all_basic_tests()