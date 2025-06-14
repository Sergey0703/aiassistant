# ====================================
# ФАЙЛ: backend/app/dependencies.py (ПОЛНАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
Зависимости и инициализация сервисов
"""

import logging
import sys
import os
import time
import json
import asyncio
from typing import Optional, List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

# ====================================
# КЛАССЫ-ЗАГЛУШКИ ДЛЯ НЕДОСТУПНЫХ СЕРВИСОВ
# ====================================

class FallbackDocumentService:
    """Заглушка для document service когда основной сервис недоступен"""
    
    def __init__(self):
        self.service_type = "fallback"
        # Добавляем атрибуты, которые ожидает код
        self.vector_db = type('MockVectorDB', (), {
            'persist_directory': './fallback_db'
        })()
        logger.info("📝 Using fallback document service")
    
    async def search(self, query: str, category: str = None, limit: int = 5):
        """Заглушка для поиска документов"""
        logger.warning(f"Fallback search called with query: {query}")
        
        # Возвращаем демо результаты
        demo_results = [
            {
                "content": f"Demo search result for '{query}'. Install document processing dependencies for real search.",
                "filename": "demo_document.txt",
                "document_id": f"demo_{int(time.time())}",
                "relevance_score": 0.95,
                "metadata": {
                    "status": "demo",
                    "category": category or "general",
                    "service": "fallback"
                }
            }
        ]
        
        return demo_results
    
    async def get_stats(self):
        """Заглушка для статистики"""
        return {
            "total_documents": 0,
            "categories": ["general", "demo"],
            "database_type": "Fallback Service",
            "error": "Document service not initialized - install dependencies",
            "available_features": [
                "Demo search responses",
                "Basic API structure", 
                "Error handling"
            ],
            "missing_dependencies": [
                "sentence-transformers (for ChromaDB)",
                "ChromaDB or SimpleVectorDB setup"
            ]
        }
    
    async def get_all_documents(self):
        """Заглушка для получения всех документов"""
        logger.warning("Fallback get_all_documents called")
        return []
    
    async def delete_document(self, doc_id: str):
        """Заглушка для удаления документа"""
        logger.warning(f"Fallback delete_document called for ID: {doc_id}")
        return False
    
    async def process_and_store_file(self, file_path: str, category: str = "general"):
        """Заглушка для обработки файла"""
        logger.warning(f"Fallback process_and_store_file called for: {file_path}")
        return False
    
    async def update_document(self, doc_id: str, content: str = None, metadata: Dict = None):
        """Заглушка для обновления документа"""
        logger.warning(f"Fallback update_document called for ID: {doc_id}")
        return False

class FallbackScraperService:
    """Заглушка для scraper service когда основной сервис недоступен"""
    
    def __init__(self):
        self.service_type = "fallback"
        self.legal_sites_config = {}
        logger.info("🌐 Using fallback scraper service")
    
    async def scrape_legal_site(self, url: str):
        """Заглушка для парсинга сайта"""
        logger.warning(f"Fallback scraper called for URL: {url}")
        
        # Создаем demo документ
        demo_content = f"""
DEMO: Legal Document from {url}

⚠️ This is a demonstration document. Real web scraping is unavailable.

To enable real scraping, install the required dependencies:
pip install aiohttp beautifulsoup4

📋 Demo Content:
This document would normally contain the actual content from the website.
In real mode, the scraper would extract legal text, articles, and regulations
from the specified URL using advanced HTML parsing techniques.

🔍 Scraped from: {url}
📅 Demo generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}
🏷️ Status: Fallback mode

For full functionality, please install the scraping dependencies.
"""
        
        # Создаем объект документа
        return type('DemoDocument', (), {
            'url': url,
            'title': f'DEMO: Legal Document from {url}',
            'content': demo_content.strip(),
            'metadata': {
                'status': 'demo',
                'real_scraping': False,
                'scraped_at': time.time(),
                'service': 'fallback',
                'url': url,
                'demo_version': '2.0'
            },
            'category': 'demo'
        })()
    
    async def scrape_multiple_urls(self, urls: List[str], delay: float = 1.0):
        """Заглушка для парсинга нескольких URL"""
        logger.warning(f"Fallback bulk scraper called for {len(urls)} URLs")
        
        results = []
        for i, url in enumerate(urls):
            if i > 0 and delay > 0:
                await asyncio.sleep(delay)
            
            doc = await self.scrape_legal_site(url)
            results.append(doc)
        
        return results
    
    async def validate_url(self, url: str):
        """Заглушка для валидации URL"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            return {
                "url": url,
                "valid": bool(parsed.scheme and parsed.netloc),
                "reachable": False,  # В fallback режиме не проверяем реальную доступность
                "issues": ["Real URL validation unavailable in fallback mode"],
                "warnings": ["Install aiohttp for real URL validation"],
                "service": "fallback"
            }
        except Exception as e:
            return {
                "url": url,
                "valid": False,
                "issues": [f"URL validation error: {e}"],
                "service": "fallback"
            }
    
    def get_stats(self):
        """Статистика fallback scraper"""
        return {
            "service_type": "fallback",
            "real_scraping_available": False,
            "demo_mode": True,
            "supported_features": [
                "Demo document generation",
                "URL validation",
                "Bulk processing simulation"
            ],
            "missing_dependencies": [
                "aiohttp",
                "beautifulsoup4"
            ]
        }

# ====================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ СЕРВИСОВ
# ====================================

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
    
    # ====================================
    # ИНИЦИАЛИЗАЦИЯ СЕРВИСА ДОКУМЕНТОВ
    # ====================================
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
                try:
                    from services.document_processor import DocumentService
                    document_service = DocumentService(settings.SIMPLE_DB_PATH)
                    CHROMADB_ENABLED = False
                    logger.info("✅ SimpleVectorDB service initialized")
                except ImportError as e2:
                    logger.error(f"SimpleVectorDB also not available: {e2}")
                    document_service = None
        else:
            # Принудительно используем SimpleVectorDB
            try:
                from services.document_processor import DocumentService
                document_service = DocumentService(settings.SIMPLE_DB_PATH)
                CHROMADB_ENABLED = False
                logger.info("✅ SimpleVectorDB service initialized (forced)")
            except ImportError as e:
                logger.error(f"SimpleVectorDB not available: {e}")
                document_service = None
        
        if document_service:
            SERVICES_AVAILABLE = True
        
    except Exception as e:
        logger.error(f"❌ Error initializing document service: {e}")
        document_service = None
        SERVICES_AVAILABLE = False
        CHROMADB_ENABLED = False
    
    # ====================================
    # ИНИЦИАЛИЗАЦИЯ СЕРВИСА ПАРСИНГА
    # ====================================
    try:
        from services.scraper_service import LegalSiteScraper
        scraper = LegalSiteScraper()
        logger.info("✅ Web scraper service initialized")
    except Exception as e:
        logger.error(f"❌ Error initializing scraper service: {e}")
        scraper = None
    
    # ====================================
    # ФИНАЛЬНЫЙ СТАТУС
    # ====================================
    logger.info(f"📊 Services status:")
    logger.info(f"   Document service: {'✅' if document_service else '❌'}")
    logger.info(f"   ChromaDB enabled: {'✅' if CHROMADB_ENABLED else '❌'}")
    logger.info(f"   Scraper service: {'✅' if scraper else '❌'}")
    logger.info(f"   Overall available: {'✅' if SERVICES_AVAILABLE else '❌'}")

# ====================================
# DEPENDENCY FUNCTIONS
# ====================================

def get_document_service():
    """Dependency для получения сервиса документов"""
    if not document_service:
        # Вместо RuntimeError создаем заглушку
        logger.debug("Using fallback document service")
        return FallbackDocumentService()
    return document_service

def get_scraper_service():
    """Dependency для получения сервиса парсинга"""
    if not scraper:
        # Вместо RuntimeError создаем заглушку
        logger.debug("Using fallback scraper service") 
        return FallbackScraperService()
    return scraper

def get_services_status():
    """Dependency для получения статуса сервисов"""
    return {
        "document_service_available": document_service is not None,
        "scraper_available": scraper is not None,
        "chromadb_enabled": CHROMADB_ENABLED,
        "services_available": SERVICES_AVAILABLE,
        "fallback_mode": document_service is None or scraper is None
    }

# ====================================
# ДОПОЛНИТЕЛЬНЫЕ UTILITY FUNCTIONS
# ====================================

async def get_system_health():
    """Получает детальную информацию о здоровье системы"""
    status = get_services_status()
    
    health_info = {
        "overall_status": "healthy" if status["services_available"] else "degraded",
        "services": status,
        "dependencies": {
            "fastapi": True,  # Если мы дошли до сюда, FastAPI работает
            "pydantic": True, # Аналогично для Pydantic
        },
        "features": {
            "document_processing": status["document_service_available"],
            "web_scraping": status["scraper_available"], 
            "vector_search": status["chromadb_enabled"],
            "demo_mode": not status["services_available"]
        }
    }
    
    # Проверяем опциональные зависимости
    optional_deps = {
        "sentence_transformers": False,
        "aiohttp": False,
        "beautifulsoup4": False,
        "chromadb": False
    }
    
    for dep in optional_deps:
        try:
            __import__(dep)
            optional_deps[dep] = True
        except ImportError:
            pass
    
    health_info["dependencies"].update(optional_deps)
    
    return health_info

async def get_service_recommendations():
    """Возвращает рекомендации по улучшению сервисов"""
    status = get_services_status()
    recommendations = []
    
    if not status["document_service_available"]:
        recommendations.append({
            "priority": "high",
            "category": "document_processing",
            "message": "Install sentence-transformers for full document processing",
            "command": "pip install sentence-transformers"
        })
    
    if not status["scraper_available"]:
        recommendations.append({
            "priority": "medium", 
            "category": "web_scraping",
            "message": "Install web scraping dependencies for real website parsing",
            "command": "pip install aiohttp beautifulsoup4"
        })
    
    if not status["chromadb_enabled"] and status["document_service_available"]:
        recommendations.append({
            "priority": "low",
            "category": "performance",
            "message": "ChromaDB provides better vector search performance",
            "command": "pip install chromadb"
        })
    
    if not recommendations:
        recommendations.append({
            "priority": "info",
            "category": "status", 
            "message": "All services are running optimally",
            "command": None
        })
    
    return recommendations

def create_fallback_response(service_name: str, operation: str, **kwargs):
    """Создает стандартизированный fallback ответ"""
    return {
        "service": service_name,
        "operation": operation,
        "status": "fallback",
        "message": f"{service_name} is running in demo mode",
        "data": kwargs.get("data", {}),
        "recommendations": [
            f"Install required dependencies for full {service_name} functionality"
        ],
        "timestamp": time.time()
    }

# ====================================
# ЭКСПОРТ
# ====================================

__all__ = [
    "init_services",
    "get_document_service", 
    "get_scraper_service",
    "get_services_status",
    "get_system_health",
    "get_service_recommendations",
    "FallbackDocumentService",
    "FallbackScraperService",
    "SERVICES_AVAILABLE",
    "CHROMADB_ENABLED",
    "document_service",
    "scraper"
]