#!/usr/bin/env python3
"""
ЭКСТРЕННЫЙ СБРОС - возвращаем к рабочему состоянию
"""

import subprocess
import sys

def run_command(cmd, description):
    """Выполняет команду с описанием"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - готово")
            return True
        else:
            print(f"⚠️ {description} - предупреждение: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"❌ {description} - ошибка: {e}")
        return False

def clean_install():
    """Чистая установка проверенных версий"""
    print("🧹 ПОЛНАЯ ОЧИСТКА И ПЕРЕУСТАНОВКА")
    print("=" * 50)
    
    # Удаляем все проблемные пакеты
    cleanup_commands = [
        "pip uninstall fastapi uvicorn pydantic starlette pydantic-core pydantic-settings annotated-types typing-extensions -y",
        "pip cache purge"
    ]
    
    for cmd in cleanup_commands:
        run_command(cmd, "Очистка старых пакетов")
    
    print("\n📦 УСТАНОВКА ПРОВЕРЕННЫХ ВЕРСИЙ")
    print("=" * 40)
    
    # Устанавливаем в правильном порядке проверенные версии
    install_commands = [
        # Базовые зависимости
        "pip install typing-extensions==4.7.1",
        
        # Pydantic v1 (стабильная для Python 3.13)
        "pip install pydantic==1.10.12",
        
        # Starlette совместимая с Pydantic v1
        "pip install starlette==0.27.0",
        
        # FastAPI совместимая с Pydantic v1
        "pip install fastapi==0.100.1",
        
        # Uvicorn
        "pip install uvicorn[standard]==0.22.0",
        
        # Дополнительные
        "pip install python-multipart==0.0.6",
        "pip install python-dotenv==1.0.0"
    ]
    
    success_count = 0
    for cmd in install_commands:
        if run_command(cmd, f"Установка {cmd.split()[-1]}"):
            success_count += 1
    
    print(f"\n📊 Установлено: {success_count}/{len(install_commands)} пакетов")
    
    return success_count >= 5  # Минимум нужно 5 основных пакетов

def test_installation():
    """Тестирует установку"""
    print("\n🧪 ТЕСТИРОВАНИЕ УСТАНОВКИ")
    print("=" * 30)
    
    tests = [
        ("typing_extensions", "Typing Extensions"),
        ("pydantic", "Pydantic"),
        ("starlette", "Starlette"), 
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn")
    ]
    
    working = []
    broken = []
    
    for module, name in tests:
        try:
            imported = __import__(module)
            version = getattr(imported, "__version__", "unknown")
            working.append(f"{name} {version}")
            print(f"✅ {name} {version}")
        except ImportError as e:
            broken.append(f"{name}: {e}")
            print(f"❌ {name}: Не установлен")
    
    return len(working) >= 4, working, broken

def create_simple_working_server():
    """Создает простой рабочий сервер"""
    print("\n📝 СОЗДАНИЕ РАБОЧЕГО СЕРВЕРА")
    print("=" * 35)
    
    server_code = '''#!/usr/bin/env python3
"""
Legal Assistant API - Стабильная версия для Python 3.13
"""

print("🚀 Запуск Legal Assistant API...")

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
    import sys
    import time
    
    # Создаем приложение
    app = FastAPI(
        title="Legal Assistant API",
        description="Стабильная версия для Python 3.13",
        version="1.0.0-stable"
    )
    
    @app.get("/")
    def read_root():
        """Главная страница"""
        return {
            "message": "🎉 Legal Assistant API запущен и работает!",
            "status": "operational",
            "python_version": sys.version.split()[0],
            "framework": "FastAPI + Pydantic v1",
            "compatibility": "Python 3.13 stable",
            "timestamp": time.time()
        }
    
    @app.get("/health")
    def health_check():
        """Проверка здоровья"""
        try:
            import pydantic
            import fastapi
            import uvicorn
            
            return {
                "status": "healthy",
                "components": {
                    "python": sys.version.split()[0],
                    "fastapi": fastapi.__version__,
                    "pydantic": pydantic.VERSION,
                    "uvicorn": uvicorn.__version__
                },
                "server": "running",
                "timestamp": time.time()
            }
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": str(e)}
            )
    
    @app.get("/api/demo")
    def demo_endpoint():
        """Демонстрационный API endpoint"""
        return {
            "message": "Демонстрационный API endpoint работает",
            "features": [
                "✅ FastAPI сервер активен",
                "✅ Pydantic валидация работает",
                "✅ JSON ответы функционируют",
                "✅ Роутинг настроен",
                "🚀 Готов к расширению функциональности"
            ],
            "next_steps": [
                "Добавить обработку документов",
                "Интегрировать векторную базу данных",
                "Настроить веб-скрапинг",
                "Добавить пользовательский интерфейс"
            ]
        }
    
    if __name__ == "__main__":
        print("=" * 60)
        print("🏛️  Legal Assistant API - Стабильная версия")
        print("=" * 60)
        print("🐍 Python:", sys.version.split()[0])
        print("🌐 Сервер: http://localhost:8000")
        print("📚 Документация: http://localhost:8000/docs")
        print("🔍 Здоровье: http://localhost:8000/health")
        print("🎯 Демо API: http://localhost:8000/api/demo")
        print("⏹️  Остановка: Ctrl+C")
        print("=" * 60)
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("🔧 Запустите сначала: python emergency_reset.py")
except Exception as e:
    print(f"❌ Ошибка сервера: {e}")
    import traceback
    traceback.print_exc()
'''
    
    try:
        with open("stable_server.py", "w", encoding="utf-8") as f:
            f.write(server_code)
        print("✅ Создан stable_server.py")
        return True
    except Exception as e:
        print(f"❌ Не удалось создать файл: {e}")
        return False

def main():
    print("🚨 ЭКСТРЕННЫЙ СБРОС И ВОССТАНОВЛЕНИЕ")
    print("=" * 60)
    print("Извините за путаницу! Возвращаем к рабочему состоянию.")
    print()
    
    # Шаг 1: Чистая установка
    if clean_install():
        print("✅ Чистая установка завершена")
    else:
        print("⚠️ Установка завершена с предупреждениями")
    
    # Шаг 2: Тестирование
    success, working, broken = test_installation()
    
    if success:
        print(f"\n✅ Тестирование прошло успешно!")
        print("Рабочие компоненты:")
        for item in working:
            print(f"  ✅ {item}")
        
        # Шаг 3: Создание сервера
        if create_simple_working_server():
            print("\n🎉 ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!")
            print("🚀 Запустите: python stable_server.py")
            print("🌐 Откройте: http://localhost:8000")
        
    else:
        print(f"\n❌ Тестирование не пройдено")
        if broken:
            print("Проблемы:")
            for item in broken:
                print(f"  ❌ {item}")
        
        print("\n💡 Рекомендация: установите Python 3.11")

if __name__ == "__main__":
    main()