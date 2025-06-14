# ====================================
# ФАЙЛ: backend/app/__init__.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
FastAPI Application Factory - Создание и настройка приложения
"""

import logging
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any

# Добавляем пути для импорта
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

logger = logging.getLogger(__name__)

def create_app() -> "FastAPI":
    """
    Создает и настраивает FastAPI приложение
    """
    try:
        # Импорты FastAPI
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        
        logger.info("🚀 Creating FastAPI application...")
        
        # Загружаем конфигурацию
        try:
            from app.config import settings, API_METADATA, API_TAGS
            app_config = {
                "title": API_METADATA["title"],
                "version": API_METADATA["version"], 
                "description": API_METADATA["description"],
                "openapi_tags": API_TAGS
            }
        except ImportError as e:
            logger.warning(f"Config import failed: {e}, using defaults")
            app_config = {
                "title": "Legal Assistant API",
                "version": "2.0.0",
                "description": "AI Legal Assistant with document processing"
            }
        
        # Создаем приложение
        app = FastAPI(**app_config)
        
        # Отслеживаем статус инициализации
        initialization_status = {
            "config_loaded": 'settings' in locals(),
            "services_initialized": False,
            "api_routes_loaded": False,
            "middleware_loaded": False,
            "errors": []
        }
        
        # Настраиваем CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=getattr(settings, 'CORS_ORIGINS', ["*"]) if 'settings' in locals() else ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Инициализируем сервисы
        try:
            from app.dependencies import init_services
            import asyncio
            
            # Создаем event loop если его нет
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Инициализируем сервисы асинхронно
            if loop.is_running():
                # Если loop уже запущен, создаем задачу
                asyncio.create_task(init_services())
            else:
                # Если loop не запущен, запускаем синхронно
                loop.run_until_complete(init_services())
                
            logger.info("✅ Services initialized")
            initialization_status["services_initialized"] = True
            
        except Exception as e:
            error_msg = f"Services initialization failed: {e}"
            logger.error(f"❌ {error_msg}")
            initialization_status["errors"].append(error_msg)
        
        # Отслеживаем статус инициализации
        initialization_status = {
            "config_loaded": 'settings' in locals(),
            "services_initialized": False,
            "api_routes_loaded": False,
            "middleware_loaded": False,
            "errors": []
        }

        # Базовые маршруты
        @app.get("/")
        async def root():
            """Корневой endpoint с полной информацией о статусе"""
            status = "healthy" if all([
                initialization_status["config_loaded"],
                initialization_status["services_initialized"],
                initialization_status["api_routes_loaded"]
            ]) else "degraded"
            
            response = {
                "message": "Legal Assistant API",
                "version": app_config.get("version", "2.0.0"),
                "status": status,
                "docs": "/docs",
                "redoc": "/redoc",
                "initialization": initialization_status
            }
            
            # Добавляем предупреждения если есть проблемы
            if status == "degraded":
                response["warnings"] = [
                    "⚠️ API работает в ограниченном режиме",
                    "Некоторые функции могут быть недоступны",
                    "Проверьте установку зависимостей"
                ]
                if initialization_status["errors"]:
                    response["errors"] = initialization_status["errors"]
            
            return response
        
        @app.get("/health")
        async def health_check():
            """Проверка здоровья системы с детальной диагностикой"""
            try:
                from app.dependencies import get_services_status
                services_status = get_services_status()
                
                # Определяем общий статус
                overall_status = "healthy"
                issues = []
                
                if not initialization_status["api_routes_loaded"]:
                    overall_status = "unhealthy"
                    issues.append("API routes not loaded")
                
                if not initialization_status["services_initialized"]:
                    overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
                    issues.append("Services not initialized")
                
                if not services_status.get("document_service_available", False):
                    if overall_status == "healthy":
                        overall_status = "degraded"
                    issues.append("Document service unavailable")
                
                response = {
                    "status": overall_status,
                    "timestamp": time.time(),
                    "services": services_status,
                    "initialization": initialization_status,
                    "version": app_config.get("version", "2.0.0")
                }
                
                if issues:
                    response["issues"] = issues
                    response["recommendations"] = [
                        "Check server logs for detailed errors",
                        "Verify all dependencies are installed",
                        "Restart the server after fixing issues"
                    ]
                
                status_code = 200 if overall_status == "healthy" else (503 if overall_status == "unhealthy" else 207)
                
                return JSONResponse(content=response, status_code=status_code)
                
            except Exception as e:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unhealthy", 
                        "error": str(e),
                        "timestamp": time.time(),
                        "message": "Health check failed - server may have serious issues"
                    }
                )
        
        # Подключаем API роутеры
        try:
            from api import configure_fastapi_app
            configure_fastapi_app(app)
            logger.info("✅ API routes configured")
            initialization_status["api_routes_loaded"] = True
        except Exception as e:
            error_msg = f"Failed to configure API routes: {e}"
            logger.error(f"❌ {error_msg}")
            initialization_status["errors"].append(error_msg)
            
            # Добавляем четкое предупреждение вместо скрытого fallback
            @app.get("/api/status")
            async def api_status():
                return {
                    "status": "❌ API routes NOT CONFIGURED",
                    "error": str(e),
                    "message": "Install missing dependencies and restart server",
                    "recommendations": [
                        "Run: pip install fastapi uvicorn pydantic",
                        "Check logs for detailed errors",
                        "Ensure all files are present in api/ directory"
                    ]
                }
        
        # Настраиваем middleware
        try:
            from app.middleware import setup_middleware
            setup_middleware(app)
            logger.info("✅ Middleware configured")
            initialization_status["middleware_loaded"] = True
        except Exception as e:
            error_msg = f"Middleware setup failed: {e}"
            logger.warning(f"⚠️ {error_msg}")
            initialization_status["errors"].append(error_msg)
        
        # Обработчик ошибок
        @app.exception_handler(Exception)
        async def global_exception_handler(request, exc):
            logger.error(f"Global exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "type": type(exc).__name__,
                    "timestamp": time.time()
                }
            )
        
        logger.info("✅ FastAPI application created successfully")
        return app
        
    except ImportError as e:
        logger.error(f"❌ Missing dependencies: {e}")