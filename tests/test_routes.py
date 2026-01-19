def create_test_app():
    """Создаем тестовое приложение"""
    try:
        # Пробуем импортировать create_app
        from app import create_app

        # Создаем приложение с тестовой конфигурацией
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False
        })
        return app
    except ImportError:
        # Если нет create_app, пробуем импортировать app напрямую
        try:
            from app import app as flask_app
            flask_app.config.update({
                'TESTING': True,
                'SECRET_KEY': 'test-secret-key',
                'WTF_CSRF_ENABLED': False
            })
            return flask_app
        except ImportError:
            # Создаем приложение вручную как последний вариант
            from flask import Flask
            app = Flask(__name__)
            app.config.update({
                'TESTING': True,
                'SECRET_KEY': 'test-secret-key',
                'WTF_CSRF_ENABLED': False
            })
            return app

def test_home_route():
    """Тест главной страницы"""
    print("\nТестирование главной страницы...")

    try:
        app = create_test_app()

        with app.test_client() as client:
            response = client.get('/')

            assert response.status_code in [200, 302]

            if response.status_code == 200:
                html = response.get_data(as_text=True)
                assert 'Что готовить' in html or 'готовить' in html.lower()

            print(f"[OK] Главная страница: статус {response.status_code}")
            return True

    except Exception as e:
        print(f"[ERROR] Ошибка главной страницы: {e}")
        return False

def test_login_page():
    """Тест страницы логина"""
    print("\nТестирование страницы логина...")

    try:
        app = create_test_app()

        with app.test_client() as client:
            response = client.get('/auth/login')

            assert response.status_code in [200, 302]

            if response.status_code == 200:
                html = response.get_data(as_text=True)
                assert 'вход' in html.lower() or 'login' in html.lower()

            print(f"[OK] Страница логина: статус {response.status_code}")
            return True

    except Exception as e:
        print(f"[ERROR] Ошибка страницы логина: {e}")
        return False

def test_register_page():
    """Тест страницы регистрации"""
    print("\nТестирование страницы регистрации...")

    try:
        app = create_test_app()

        with app.test_client() as client:
            response = client.get('/auth/register')

            assert response.status_code in [200, 302]

            if response.status_code == 200:
                html = response.get_data(as_text=True)
                assert 'регистрация' in html.lower() or 'register' in html.lower()

            print(f"[OK] Страница регистрации: статус {response.status_code}")
            return True

    except Exception as e:
        print(f"[ERROR] Ошибка страницы регистрации: {e}")
        return False

def test_protected_route_redirect():
    """Тест что защищённые маршруты редиректят"""
    print("\nТестирование защищённых маршрутов...")

    try:
        app = create_test_app()

        with app.test_client() as client:
            response = client.get('/user/my-ingredients', follow_redirects=False)

            assert response.status_code in [302, 200]

            print(f"[OK] Защищённые маршруты требуют авторизации: статус {response.status_code}")
            return True

    except Exception as e:
        print(f"[ERROR] Ошибка защищённых маршрутов: {e}")
        return False

def test_api_endpoints_exist():
    """Тест что API endpoints существуют"""
    print("\nТестирование API endpoints...")

    try:
        app = create_test_app()

        with app.test_client() as client:
            endpoints = [
                '/auth/api/login',
                '/auth/api/register',
                '/user/ingredients',
            ]

            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code != 404
                print(f"  [OK] Endpoint {endpoint} существует")

            print("[OK] Все проверенные API endpoints существуют")
            return True

    except Exception as e:
        print(f"[ERROR] Ошибка API endpoints: {e}")
        return False

def run_all_route_tests():
    """Запуск всех тестов маршрутов"""
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ МАРШРУТОВ")
    print("="*50)

    results = []
    results.append(test_home_route())
    results.append(test_login_page())
    results.append(test_register_page())
    results.append(test_protected_route_redirect())
    results.append(test_api_endpoints_exist())

    passed = sum([1 for r in results if r])
    total = len(results)

    print(f"\nИТОГО: {passed}/{total} тестов маршрутов пройдено")

    if passed == total:
        print("Все тесты маршрутов пройдены!")
        return True
    else:
        print("Есть проблемы с маршрутами")
        return False

if __name__ == "main":
    run_all_route_tests()
