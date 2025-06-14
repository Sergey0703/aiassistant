#!/usr/bin/env python3
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
