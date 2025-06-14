# ====================================
# ФАЙЛ: backend/app/dependencies.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для зависимостей и сервисов
# ====================================

"""
Зависимости и инициализация сервисов
"""

import logging
import sys
import os
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Глобальные сервисы
document_service: Optional[object] = None
scraper: Optional[object] = None
SERVICES_AVAILABLE: bool = False
CHROMADB_ENABLED: bool = False

async def init_services():
    """Инициализация всех сервисов приложения"""
    global document_service, scraper, SERVICES_AVAILABLE, CHROMADB_ENABLED
    
    logger.info("🔧 Initializing services...")
    
    # Добавляем текущую папку в Python path
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    
    # Инициализация сервисов документов
    try:
        if settings.USE_CHROMADB:
            # Пытаемся использовать ChromaDB
            try:
                from services.chroma_service import DocumentService
                document_service = DocumentService(settings.CHROMADB_PATH)
                CHROMADB_ENABLED = True
                logger.info("✅ ChromaDB service initialized")
            except ImportError as e:
                logger.warning(f"ChromaDB not available, falling back to SimpleVectorDB: {e}")
                from services.document_processor import DocumentService
                document_service = DocumentService(settings.SIMPLE_DB_PATH)
                CHROMADB_ENABLED = False
                logger.info("✅ SimpleVectorDB service initialized")
        else:
            # Принудительно используем SimpleVectorDB
            from services.document_processor import DocumentService
            document_service = DocumentService(settings.SIMPLE_DB_PATH)
            CHROMADB_ENABLED = False
            logger.info("✅ SimpleVectorDB service initialized (forced)")
            
        SERVICES_AVAILABLE = True
        
    except Exception as e:
        logger.error(f"❌ Error initializing document service: {e}")
        document_service = None
        SERVICES_AVAILABLE = False
        CHROMADB_ENABLED = False
    
    # Инициализация сервиса парсинга
    try:
        from services.scraper_service import LegalSiteScraper
        scraper = LegalSiteScraper()
        logger.info("✅ Web scraper service initialized")
    except Exception as e:
        logger.error(f"❌ Error initializing scraper service: {e}")
        scraper = None
    
    # Логируем финальный статус
    logger.info(f"📊 Services status:")
    logger.info(f"   Document service: {'✅' if document_service else '❌'}")
    logger.info(f"   ChromaDB enabled: {'✅' if CHROMADB_ENABLED else '❌'}")
    logger.info(f"   Scraper service: {'✅' if scraper else '❌'}")
    logger.info(f"   Overall available: {'✅' if SERVICES_AVAILABLE else '❌'}")

def get_document_service():
    """Dependency для получения сервиса документов"""
    if not document_service:
        raise RuntimeError("Document service not available")
    return document_service

def get_scraper_service():
    """Dependency для получения сервиса парсинга"""
    if not scraper:
        raise RuntimeError("Scraper service not available")
    return scraper

def get_services_status():
    """Dependency для получения статуса сервисов"""
    return {
        "document_service_available": document_service is not None,
        "scraper_available": scraper is not None,
        "chromadb_enabled": CHROMADB_ENABLED,
        "services_available": SERVICES_AVAILABLE
    }