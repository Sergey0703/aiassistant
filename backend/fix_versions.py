#!/usr/bin/env python3
# ====================================
# ФАЙЛ: backend/fix_versions.py
# Исправление конфликтов версий
# ====================================

"""
Исправляет конфликты версий пакетов
"""

import subprocess
import sys

def run_pip_command(command):
    """Выполняет pip команду"""
    try:
        print(f"🔧 Выполняем: {command}")
        result = subprocess.run(command.split(), capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Команда выполнена успешно")
            return True
        else:
            print(f"❌ Ошибка: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    print("🔧 Исправление версий пакетов...")
    print("=" * 50)
    
    # Список совместимых версий
    compatible_packages = [
        "fastapi==0.100.1",
        "uvicorn==0.22.0", 
        "pydantic==1.10.12",
        "starlette==0.27.0",
        "typing-extensions==4.7.1"
    ]
    
    print("📦 Переустанавливаем пакеты совместимыми версиями...")
    
    for package in compatible_packages:
        print(f"\n🔄 Устанавливаем {package}")
        run_pip_command(f"pip install {package} --force-reinstall --no-deps")
    
    # Проверяем совместимость
    print("\n🧪 Проверяем импорты...")
    
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI: {e}")
    
    try:
        import uvicorn
        print(f"✅ Uvicorn {uvicorn.__version__}")
    except Exception as e:
        print(f"❌ Uvicorn: {e}")
        
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.VERSION}")
    except Exception as e:
        print(f"❌ Pydantic: {e}")
    
    print("\n🚀 Пробуем создать простое приложение...")
    
    try:
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/")
        def read_root():
            return {"message": "FastAPI работает!"}
        
        print("✅ Простое приложение создано успешно")
        
        # Создаем рабочий test файл
        create_working_test()
        
        print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("Запустите: python test_server.py")
        
    except Exception as e:
        print(f"❌ Ошибка создания приложения: {e}")
        print("\n💡 Попробуйте:")
        print("pip install fastapi==0.95.2 uvicorn==0.20.0 pydantic==1.10.7")

def create_working_test():
    """Создает рабочий тестовый сервер"""
    test_code = '''#!/usr/bin/env python3
"""
Тестовый сервер для проверки FastAPI
"""

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
    import time
    
    # Создаем приложение
    app = FastAPI(
        title="Legal Assistant API - Test",
        description="Тестовая версия API",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        """Главная страница"""
        return {
            "message": "🎉 Legal Assistant API работает!",
            "status": "ok",
            "version": "test-1.0.0",
            "timestamp": time.time()
        }
    
    @app.get("/health")
    async def health():
        """Проверка здоровья"""
        return {
            "status": "healthy",
            "mode": "test",
            "dependencies": {
                "fastapi": "installed",
                "uvicorn": "installed", 
                "pydantic": "installed"
            }
        }
    
    @app.get("/api/test")
    async def api_test():
        """Тестовый API endpoint"""
        return {
            "message": "API endpoints работают",
            "features": [
                "✅ FastAPI запущен",
                "✅ Pydantic работает", 
                "✅ JSON responses работают",
                "🔧 Базовая функциональность готова"
            ]
        }
    
    if __name__ == "__main__":
        print("🚀 Запуск тестового сервера...")
        print("📍 Откройте: http://localhost:8000")
        print("📚 Документация: http://localhost:8000/docs")
        print("⏹️ Остановка: Ctrl+C")
        print("-" * 50)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите: pip install fastapi uvicorn")
except Exception as e:
    print(f"❌ Ошибка: {e}")
'''
    
    try:
        with open("test_server.py", "w", encoding="utf-8") as f:
            f.write(test_code)
        print("📝 Создан test_server.py")
    except Exception as e:
        print(f"⚠️ Не удалось создать test_server.py: {e}")

if __name__ == "__main__":
    main()