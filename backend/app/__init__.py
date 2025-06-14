# ====================================
# ФАЙЛ: backend/api/__init__.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для инициализации API пакета
# ====================================

"""
API Package - Основной пакет API endpoints для Legal Assistant
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

logger = logging.getLogger(__name__)

# Версия API
API_VERSION = "2.0.0"
API_PREFIX = "/api"

# Метаданные API
API_METADATA = {
    "title": "Legal Assistant API",
    "version": API_VERSION,
    "description": "AI-powered Legal Assistant with document processing and web scraping",
    "contact": {
        "name": "Legal Assistant Team",
        "email": "support@legalassistant.com"
    },
    "license": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
}

# Теги для группировки endpoints в документации
API_TAGS = [
    {
        "name": "User Chat",
        "description": "User chat endpoints for legal assistance"
    },
    {
        "name": "User Search", 
        "description": "Document search endpoints for users"
    },
    {
        "name": "Admin Documents",
        "description": "Document management endpoints for administrators"
    },
    {
        "name": "Admin Scraper",
        "description": "Web scraping endpoints for administrators"
    },
    {
        "name": "Admin Stats",
        "description": "Statistics and analytics endpoints for administrators"
    },
    {
        "name": "System",
        "description": "System health and information endpoints"
    }
]

class APIRegistry:
    """Реестр всех API роутеров"""
    
    def __init__(self):
        self.routers = {}
        self.routes_count = 0
        self.initialization_errors = []
    
    def register_router(self, name: str, router: APIRouter, prefix: str = "", tags: List[str] = None):
        """Регистрирует роутер в реестре"""
        try:
            self.routers[name] = {
                "router": router,
                "prefix": prefix,
                "tags": tags or [],
                "routes_count": len(router.routes),
                "registered_at": None
            }
            
            logger.debug(f"📝 Registered router '{name}' with {len(router.routes)} routes")
            
        except Exception as e:
            error_msg = f"Failed to register router '{name}': {e}"
            self.initialization_errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
    
    def get_router(self, name: str) -> Dict[str, Any]:
        """Получает информацию о роутере"""
        return self.routers.get(name)
    
    def get_all_routers(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает все зарегистрированные роутеры"""
        return self.routers.copy()
    
    def get_routes_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по всем маршрутам"""
        total_routes = sum(info["routes_count"] for info in self.routers.values())
        
        routes_by_method = {}
        routes_by_tag = {}
        
        for router_name, router_info in self.routers.items():
            router = router_info["router"]
            tags = router_info["tags"]
            
            for route in router.routes:
                if isinstance(route, APIRoute):
                    # Подсчет по методам
                    for method in route.methods:
                        routes_by_method[method] = routes_by_method.get(method, 0) + 1
                    
                    # Подсчет по тегам
                    for tag in tags:
                        routes_by_tag[tag] = routes_by_tag.get(tag, 0) + 1
        
        return {
            "total_routers": len(self.routers),
            "total_routes": total_routes,
            "routes_by_method": routes_by_method,
            "routes_by_tag": routes_by_tag,
            "initialization_errors": self.initialization_errors
        }

# Глобальный реестр API
api_registry = APIRegistry()

def load_user_routers():
    """Загружает пользовательские роутеры"""
    try:
        # Загружаем chat router
        try:
            from api.user.chat import router as chat_router
            api_registry.register_router(
                "user_chat",
                chat_router,
                prefix="/api/user",
                tags=["User Chat"]
            )
        except ImportError as e:
            logger.error(f"❌ Failed to import user chat router: {e}")
            api_registry.initialization_errors.append(f"User chat router: {e}")
        
        # Загружаем search router
        try:
            from api.user.search import router as search_router
            api_registry.register_router(
                "user_search",
                search_router,
                prefix="/api/user",
                tags=["User Search"]
            )
        except ImportError as e:
            logger.error(f"❌ Failed to import user search router: {e}")
            api_registry.initialization_errors.append(f"User search router: {e}")
        
        logger.info("✅ User routers loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error loading user routers: {e}")
        api_registry.initialization_errors.append(f"User routers loading: {e}")

def load_admin_routers():
    """Загружает административные роутеры"""
    try:
        # Загружаем documents router
        try:
            from api.admin.documents import router as documents_router
            api_registry.register_router(
                "admin_documents",
                documents_router,
                prefix="/api/admin",
                tags=["Admin Documents"]
            )
        except ImportError as e:
            logger.error(f"❌ Failed to import admin documents router: {e}")
            api_registry.initialization_errors.append(f"Admin documents router: {e}")
        
        # Загружаем scraper router
        try:
            from api.admin.scraper import router as scraper_router
            api_registry.register_router(
                "admin_scraper",
                scraper_router,
                prefix="/api/admin",
                tags=["Admin Scraper"]
            )
        except ImportError as e:
            logger.error(f"❌ Failed to import admin scraper router: {e}")
            api_registry.initialization_errors.append(f"Admin scraper router: {e}")
        
        # Загружаем stats router
        try:
            from api.admin.stats import router as stats_router
            api_registry.register_router(
                "admin_stats",
                stats_router,
                prefix="/api/admin",
                tags=["Admin Stats"]
            )
        except ImportError as e:
            logger.error(f"❌ Failed to import admin stats router: {e}")
            api_registry.initialization_errors.append(f"Admin stats router: {e}")
        
        logger.info("✅ Admin routers loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error loading admin routers: {e}")
        api_registry.initialization_errors.append(f"Admin routers loading: {e}")

def initialize_api():
    """Инициализирует все API компоненты"""
    logger.info("🚀 Initializing API package...")
    
    # Загружаем роутеры
    load_user_routers()
    load_admin_routers()
    
    # Получаем сводку
    summary = api_registry.get_routes_summary()
    
    logger.info(f"📊 API initialization completed:")
    logger.info(f"   Total routers: {summary['total_routers']}")
    logger.info(f"   Total routes: {summary['total_routes']}")
    
    if summary['initialization_errors']:
        logger.warning(f"⚠️ {len(summary['initialization_errors'])} initialization errors:")
        for error in summary['initialization_errors']:
            logger.warning(f"   - {error}")
    else:
        logger.info("✅ All routers loaded successfully")

def configure_fastapi_app(app: FastAPI):
    """Настраивает FastAPI приложение с зарегистрированными роутерами"""
    try:
        logger.info("🔧 Configuring FastAPI app with routers...")
        
        # Подключаем все зарегистрированные роутеры
        for router_name, router_info in api_registry.get_all_routers().items():
            try:
                app.include_router(
                    router_info["router"],
                    prefix=router_info["prefix"],
                    tags=router_info["tags"]
                )
                
                # Обновляем время регистрации
                router_info["registered_at"] = time.time()
                api_registry.routes_count += router_info["routes_count"]
                
                logger.debug(f"✅ Included router '{router_name}' with prefix '{router_info['prefix']}'")
                
            except Exception as e:
                logger.error(f"❌ Failed to include router '{router_name}': {e}")
                api_registry.initialization_errors.append(f"Including {router_name}: {e}")
        
        logger.info(f"🎯 FastAPI app configured with {api_registry.routes_count} total routes")
        
    except Exception as e:
        logger.error(f"❌ Error configuring FastAPI app: {e}")
        raise

def get_api_info() -> Dict[str, Any]:
    """Возвращает информацию об API"""
    import time
    
    summary = api_registry.get_routes_summary()
    
    return {
        "metadata": API_METADATA,
        "version": API_VERSION,
        "prefix": API_PREFIX,
        "summary": summary,
        "routers": {
            name: {
                "prefix": info["prefix"],
                "tags": info["tags"],
                "routes_count": info["routes_count"],
                "registered_at": info.get("registered_at")
            }
            for name, info in api_registry.get_all_routers().items()
        },
        "tags": API_TAGS,
        "status": "healthy" if not summary["initialization_errors"] else "degraded",
        "timestamp": time.time()
    }

def get_api_routes() -> List[Dict[str, Any]]:
    """Возвращает детальную информацию о всех маршрутах"""
    routes_info = []
    
    for router_name, router_info in api_registry.get_all_routers().items():
        router = router_info["router"]
        prefix = router_info["prefix"]
        tags = router_info["tags"]
        
        for route in router.routes:
            if isinstance(route, APIRoute):
                route_info = {
                    "router": router_name,
                    "path": prefix + route.path,
                    "methods": list(route.methods),
                    "name": route.name,
                    "tags": tags,
                    "summary": getattr(route, "summary", None),
                    "description": getattr(route, "description", None),
                    "deprecated": getattr(route, "deprecated", False)
                }
                routes_info.append(route_info)
    
    return routes_info

def create_system_router() -> APIRouter:
    """Создает системный роутер с информацией об API"""
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse
    
    router = APIRouter()
    
    @router.get("/system/api/info")
    async def get_system_api_info():
        """Получить информацию об API"""
        try:
            return get_api_info()
        except Exception as e:
            return {
                "error": str(e),
                "status": "error",
                "fallback": True
            }
    
    @router.get("/system/api/routes")
    async def get_system_api_routes():
        """Получить список всех маршрутов API"""
        return {
            "routes": get_api_routes(),
            "total": len(get_api_routes())
        }
    
    @router.get("/system/api/health")
    async def get_api_health():
        """Проверить здоровье API"""
        info = get_api_info()
        
        health_status = {
            "status": info["status"],
            "api_version": info["version"],
            "total_routers": info["summary"]["total_routers"],
            "total_routes": info["summary"]["total_routes"],
            "errors_count": len(info["summary"]["initialization_errors"]),
            "timestamp": info["timestamp"]
        }
        
        status_code = 200 if info["status"] == "healthy" else 503
        
        return JSONResponse(
            content=health_status,
            status_code=status_code
        )
    
    @router.get("/system/api/errors")
    async def get_api_errors():
        """Получить ошибки инициализации API"""
        return {
            "errors": api_registry.initialization_errors,
            "count": len(api_registry.initialization_errors)
        }
    
    return router

# Автоматическая инициализация при импорте
try:
    initialize_api()
    
    # Регистрируем системный роутер
    system_router = create_system_router()
    api_registry.register_router(
        "system",
        system_router,
        prefix="",
        tags=["System"]
    )
    
except Exception as e:
    logger.error(f"❌ API package initialization failed: {e}")

# Экспорт основных компонентов
__all__ = [
    # Метаданные
    "API_VERSION",
    "API_PREFIX", 
    "API_METADATA",
    "API_TAGS",
    
    # Классы
    "APIRegistry",
    "api_registry",
    
    # Функции инициализации
    "initialize_api",
    "configure_fastapi_app",
    "load_user_routers",
    "load_admin_routers",
    
    # Информационные функции
    "get_api_info",
    "get_api_routes",
    "create_system_router",
    
    # Системные компоненты
    "system_router"
]

logger.debug(f"📦 API package initialized with {len(__all__)} exported items")