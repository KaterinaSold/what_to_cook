def test_user_model():
    """Тест модели пользователя"""
    print("\nТестирование модели User...")

    try:
        from app.models import User

        user = User(
            username="testuser",
            email="test@example.com",
            is_admin=False
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_admin == False

        assert "testuser" in str(user)

        print("[OK] Модель User работает корректно")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка в модели User: {e}")
        return False

def test_ingredient_model():
    """Тест модели ингредиента"""
    print("\nТестирование модели Ingredient...")

    try:
        from app.models import Ingredient

        ingredient = Ingredient(
            name="Куриная грудка",
            calories=165.0,
            proteins=31.0,
            fats=3.6,
            carbs=0.0,
            user_id=1,
            is_public=True
        )

        assert ingredient.name == "Куриная грудка"
        assert ingredient.calories == 165.0
        assert ingredient.proteins == 31.0
        assert ingredient.fats == 3.6
        assert ingredient.carbs == 0.0
        assert ingredient.is_public == True

        print("[OK] Модель Ingredient работает корректно")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка в модели Ingredient: {e}")
        return False

def test_recipe_model():
    """Тест модели рецепта"""
    print("\nТестирование модели Recipe...")

    try:
        from app.models import Recipe

        recipe = Recipe(
            name="Курица с овощами",
            description="Вкусный рецепт",
            instructions="Приготовить и подать",
            user_id=1,
            is_public=True
        )

        assert recipe.name == "Курица с овощами"
        assert recipe.description == "Вкусный рецепт"
        assert recipe.instructions == "Приготовить и подать"
        assert recipe.is_public == True

        print("[OK] Модель Recipe работает корректно")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка в модели Recipe: {e}")
        return False

def test_user_password():
    """Тест установки и проверки пароля"""
    print("\nТестирование паролей...")

    try:
        from app.models import User

        user = User(username="test", email="test@test.com")

        user.set_password("secret123")

        assert user.password_hash is not None
        assert user.password_hash != "secret123"

        assert user.check_password("secret123") == True
        assert user.check_password("wrongpass") == False

        print("[OK] Работа с паролями корректна")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка работы с паролями: {e}")
        return False

def run_all_model_tests():
    """Запуск всех тестов моделей"""
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ МОДЕЛЕЙ")
    print("="*50)

    results = []
    results.append(test_user_model())
    results.append(test_ingredient_model())
    results.append(test_recipe_model())
    results.append(test_user_password())

    passed = sum([1 for r in results if r])
    total = len(results)

    print(f"\nИТОГО: {passed}/{total} тестов моделей пройдено")

    if passed == total:
        print("Все тесты моделей пройдены!")
        return True
    else:
        print("Есть проблемы с моделями")
        return False

if __name__ == "main":
    run_all_model_tests()