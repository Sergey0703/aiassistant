#!/usr/bin/env python3
"""
Исправление совместимости Python 3.13 + Pydantic
"""

import subprocess
import sys

def run_command(cmd):
    """Выполняет команду pip"""
    try:
        print(f"🔧 {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Успешно")
            return True
        else:
            print(f"❌ Ошибка: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {e}")
        return False

def main():
    print("🔧 Исправление совместимости Python 3.13")
    print("=" * 50)
    
    # Вариант 1: Обновляем до совместимых версий
    print("\n📦 Вариант 1: Совместимые версии...")
    
    commands_v1 = [
        "pip uninstall fastapi uvicorn pydantic starlette -y",
        "pip install pydantic==2.5.0 --force-reinstall",
        "pip install fastapi==0.104.1 --force-reinstall", 
        "pip install uvicorn==0.24.0 --force-reinstall"
    ]
    
    success_v1 = True
    for cmd in commands_v1:
        if not run_command(cmd):
            success_v1 = False
    
    if success_v1:
        print("\n🧪 Тестируем Вариант 1...")
        if test_imports():
            create_working_server()
            return
    
    print("\n❌ Вариант 1 не сработал")
    
    # Вариант 2: Downgrade к старым совместимым версиям
    print("\n📦 Вариант 2: Старые стабильные версии...")
    
    commands_v2 = [
        "pip uninstall fastapi uvicorn pydantic starlette -y",
        "pip install typing-extensions==4.7.1",
        "pip install pydantic==1.10.12",
        "pip install starlette==0.27.0", 
        "pip install fastapi==0.100.1",
        "pip install uvicorn==0.22.0"
    ]
    
    success_v2 = True
    for cmd in commands_v2:
        if not run_command(cmd):
            success_v2 = False
    
    if success_v2:
        print("\n🧪 Тестируем Вариант 2...")
        if test_imports():
            create_working_server()
            return
    
    print("\n❌ Вариант 2 не сработал")
    
    # Вариант 3: Минимальный набор
    print("\n📦 Вариант 3: Экстренный минимум...")
    
    commands_v3 = [
        "pip uninstall fastapi uvicorn pydantic starlette -y",
        "pip install pydantic==1.9.2",
        "pip install starlette==0.20.4",
        "pip install fastapi==0.85.0", 
        "pip install uvicorn==0.18.3"
    ]
    
    for cmd in commands_v3:
        run_command(cmd)
    
    print("\n🧪 Тестируем Вариант 3...")
    if test_imports():
        create_working_server()
    else:
        print("\n💥 Все варианты не сработали!")
        print("🔧 Попробуйте Python 3.11 или 3.10")

def test_imports():
    """Тестирует импорты"""
    try:
        print("🧪 Проверяем импорты...")
        
        # Проверяем каждый пакет отдельно
        exec("import pydantic; print(f'✅ Pydantic {pydantic.VERSION}')")
        exec("import starlette; print(f'✅ Starlette {starlette.__version__}')")
        exec("import fastapi; print(f'✅ FastAPI {fastapi.__version__}')")
        exec("import uvicorn; print(f'✅ Uvicorn {uvicorn.__version__}')")
        
        # Проверяем создание приложения
        exec("from fastapi import FastAPI; app = FastAPI(); print('✅ Приложение создано')")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def create_working_server():
    """Создает рабочий сервер"""
    print("\n📝 Создаем рабочий сервер...")
    
    server_code = '''#!/usr/bin/env python3
"""
Legal Assistant API - Рабочая версия
"""

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
    import time
    import sys
    
    print("🚀 Создание приложения...")
    
    app = FastAPI(
        title="Legal Assistant API",
        description="AI Legal Assistant - Working Version",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "🎉 Legal Assistant API работает!",
            "status": "working",
            "version": "1.0.0",
            "python_version": sys.version,
            "timestamp": time.time()
        }
    
    @app.get("/health")
    async def health():
        try:
            import pydantic
            import fastapi
            import uvicorn
            
            return {
                "status": "healthy",
                "components": {
                    "python": sys.version.split()[0],
                    "fastapi": fastapi.__version__,
                    "pydantic": str(pydantic.VERSION),
                    "uvicorn": uvicorn.__version__
                },
                "timestamp": time.time()
            }
        except Exception as e:
            return {"status": "degraded", "error": str(e)}
    
    @app.get("/api/test")
    async def api_test():
        return {
            "message": "API работает корректно",
            "endpoints": [
                "GET / - главная страница",
                "GET /health - статус здоровья", 
                "GET /docs - документация Swagger",
                "GET /redoc - документация ReDoc"
            ]
        }
    
    if __name__ == "__main__":
        print("=" * 60)
        print("🏛️  Legal Assistant API")
        print("=" * 60)
        print("🌐 Сервер: http://localhost:8000")
        print("📚 Документация: http://localhost:8000/docs")
        print("📖 ReDoc: http://localhost:8000/redoc")
        print("❤️ Здоровье: http://localhost:8000/health")
        print("⏹️ Остановка: Ctrl+C")
        print("=" * 60)
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=True
        )

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Переустановите пакеты: python fix_compatibility.py")
except Exception as e:
    print(f"❌ Ошибка приложения: {e}")
'''
    
    try:
        with open("working_server.py", "w", encoding="utf-8") as f:
            f.write(server_code)
        
        print("✅ Создан working_server.py")
        print("\n🎉 ГОТОВО!")
        print("🚀 Запустите: python working_server.py")
        print("🌐 Откройте: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Не удалось создать файл: {e}")

if __name__ == "__main__":
    main()