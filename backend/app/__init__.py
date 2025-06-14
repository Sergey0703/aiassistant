# ====================================
# ФАЙЛ: backend/app/__init__.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для инициализации приложения
# ====================================

"""
Application factory и конфигурация FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.dependencies import init_services
from api.user.chat import router as chat_router
from api.user.search import router as search_router
from api.admin.documents import router as documents_router
from api.admin.scraper import router as scraper_router
from api.admin.stats import router as stats_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 Legal Assistant API starting up...")
    
    # Инициализация сервисов
    await init_services()
    
    yield
    
    logger.info("🛑 Legal Assistant API shutting down...")

def create_app() -> FastAPI:
    """Factory для создания FastAPI приложения"""
    
    app = FastAPI(
        title="Legal Assistant API",
        version="2.0.0",
        description="AI Legal Assistant with document scraping and ChromaDB",
        lifespan=lifespan
    )
    
    # CORS настройка
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Подключение роутеров
    
    # User endpoints
    app.include_router(
        chat_router,
        prefix="/api/user",
        tags=["User Chat"]
    )
    
    app.include_router(
        search_router,
        prefix="/api/user",
        tags=["User Search"]
    )
    
    # Admin endpoints
    app.include_router(
        documents_router,
        prefix="/api/admin",
        tags=["Admin Documents"]
    )
    
    app.include_router(
        scraper_router,
        prefix="/api/admin",
        tags=["Admin Scraper"]
    )
    
    app.include_router(
        stats_router,
        prefix="/api/admin",
        tags=["Admin Stats"]
    )
    
    # Базовые endpoints
    @app.get("/")
    async def root():
        return {
            "message": "Legal Assistant API v2.0 with modular architecture",
            "version": "2.0.0",
            "features": [
                "Modular Document Processing",
                "Website Scraping",
                "Vector Search with ChromaDB",
                "Multi-language Support",
                "Legal Document Analysis"
            ],
            "docs": "/docs"
        }
    
    @app.get("/api/health")
    async def health_check():
        """Проверка состояния системы"""
        from app.dependencies import document_service, scraper, SERVICES_AVAILABLE, CHROMADB_ENABLED
        
        health_status = {
            "status": "healthy",
            "services": {
                "document_service": document_service is not None,
                "scraper": scraper is not None,
                "services_module": SERVICES_AVAILABLE,
                "chromadb_enabled": CHROMADB_ENABLED
            }
        }
        
        if document_service:
            try:
                stats = await document_service.get_stats()
                health_status["vector_db"] = stats
            except Exception as e:
                health_status["vector_db_error"] = str(e)
        
        return health_status
    
    logger.info("✅ FastAPI application created with modular structure")
    return app