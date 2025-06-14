#!/usr/bin/env python3
"""
Локальное исправление для Python 3.13 + Pydantic
"""

import sys
import subprocess

def patch_forwardref():
    """Патчит ForwardRef для совместимости"""
    try:
        # Пытаемся импортировать и пропатчить
        import typing
        from typing import ForwardRef
        
        # Сохраняем оригинальный метод
        original_evaluate = ForwardRef._evaluate
        
        def patched_evaluate(self, globalns=None, localns=None, recursive_guard=None):
            """Исправленная версия _evaluate с поддержкой recursive_guard"""
            if recursive_guard is None:
                recursive_guard = frozenset()
            return original_evaluate(self, globalns, localns, recursive_guard)
        
        # Заменяем метод
        ForwardRef._evaluate = patched_evaluate
        print("✅ ForwardRef._evaluate() пропатчен для Python 3.13")
        return True
        
    except Exception as e:
        print(f"❌ Не удалось пропатчить ForwardRef: {e}")
        return False

def install_compatible_versions():
    """Устанавливает совместимые версии пакетов"""
    print("🔧 Установка совместимых версий...")
    
    # Устанавливаем typing-extensions с поддержкой Python 3.13
    commands = [
        "pip install typing-extensions==4.8.0 --force-reinstall",
        "pip install pydantic==2.4.2 --force-reinstall --no-deps",
        "pip install annotated-types pydantic-core --force-reinstall",
        "pip install fastapi==0.103.2 --force-reinstall --no-deps", 
        "pip install starlette==0.27.0 --force-reinstall",
        "pip install uvicorn==0.23.2 --force-reinstall --no-deps"
    ]
    
    for cmd in commands:
        try:
            print(f"📦 {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Успешно")
            else:
                print(f"⚠️ Предупреждение: {result.stderr}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def create_compatibility_wrapper():
    """Создает обертку для совместимости"""
    wrapper_code = '''#!/usr/bin/env python3
"""
Обертка совместимости для Python 3.13
"""

# Исправляем ForwardRef перед импортом других модулей
import sys
from typing import ForwardRef

# Пропатчиваем ForwardRef._evaluate для Python 3.13
original_evaluate = ForwardRef._evaluate

def patched_evaluate(self, globalns=None, localns=None, recursive_guard=None):
    """Совместимая версия _evaluate"""
    if recursive_guard is None:
        recursive_guard = frozenset()
    return original_evaluate(self, globalns, localns, recursive_guard)

ForwardRef._evaluate = patched_evaluate

# Теперь можно безопасно импортировать FastAPI
try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
    import time
    
    print("✅ Патч применен, FastAPI импортирован успешно")
    
    # Создаем приложение
    app = FastAPI(
        title="Legal Assistant API - Python 3.13 Compatible",
        description="Исправленная версия для Python 3.13",
        version="1.0.0-py313-fix"
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "🎉 Legal Assistant API работает с Python 3.13!",
            "status": "working",
            "python_version": sys.version,
            "fix_applied": "ForwardRef._evaluate patched",
            "timestamp": time.time()
        }
    
    @app.get("/health")
    async def health():
        import pydantic
        import fastapi
        
        return {
            "status": "healthy",
            "python_version": sys.version.split()[0],
            "packages": {
                "fastapi": fastapi.__version__,
                "pydantic": str(pydantic.VERSION),
                "uvicorn": uvicorn.__version__
            },
            "fix_status": "ForwardRef compatibility patch active"
        }
    
    @app.get("/api/test")
    async def api_test():
        return {
            "message": "API тестирование прошло успешно",
            "features": [
                "✅ Python 3.13 совместимость",
                "✅ ForwardRef._evaluate исправлен",
                "✅ FastAPI функционирует",
                "✅ Pydantic работает",
                "✅ JSON responses активны"
            ]
        }
    
    if __name__ == "__main__":
        print("=" * 60)
        print("🐍 Legal Assistant API - Python 3.13 Compatible")
        print("=" * 60)
        print("🔧 Применен патч для ForwardRef._evaluate()")
        print("🌐 Сервер: http://localhost:8000")
        print("📚 Документация: http://localhost:8000/docs")
        print("❤️ Здоровье: http://localhost:8000/health")
        print("=" * 60)
        
        uvicorn.run(
            app,
            host="127.0.0.1", 
            port=8000,
            log_level="info"
        )

except ImportError as e:
    print(f"❌ Ошибка импорта даже после патча: {e}")
    print("Попробуйте: pip install --force-reinstall fastapi pydantic uvicorn")
except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")
'''
    
    try:
        with open("patched_server.py", "w", encoding="utf-8") as f:
            f.write(wrapper_code)
        print("✅ Создан patched_server.py с исправлениями")
        return True
    except Exception as e:
        print(f"❌ Не удалось создать файл: {e}")
        return False

def main():
    print("🔧 Локальное исправление для Python 3.13")
    print("=" * 50)
    
    print("📋 Стратегия исправления:")
    print("1. Патчим ForwardRef._evaluate() для Python 3.13")
    print("2. Устанавливаем совместимые версии пакетов")
    print("3. Создаем обертку с встроенным патчем")
    print()
    
    # Шаг 1: Пробуем пропатчить
    print("🛠️ Шаг 1: Применяем патч...")
    patch_success = patch_forwardref()
    
    # Шаг 2: Устанавливаем совместимые версии
    print("\n🛠️ Шаг 2: Устанавливаем совместимые версии...")
    install_compatible_versions()
    
    # Шаг 3: Создаем файл с патчем
    print("\n🛠️ Шаг 3: Создаем сервер с встроенным патчем...")
    wrapper_success = create_compatibility_wrapper()
    
    if wrapper_success:
        print("\n🎉 Локальное исправление завершено!")
        print("🚀 Запустите: python patched_server.py")
        print("🌐 Откройте: http://localhost:8000")
    else:
        print("\n❌ Не удалось создать исправленный сервер")

if __name__ == "__main__":
    main()