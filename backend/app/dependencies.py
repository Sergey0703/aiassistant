# ====================================
# ФАЙЛ: backend/app/dependencies.py (ОБНОВЛЕННАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
Зависимости и инициализация сервисов с поддержкой LLM
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

class FallbackLLMService:
    """Заглушка для LLM service когда Ollama недоступен"""
    
    def __init__(self):
        self.service_type = "fallback"
        self.ollama_available = False
        logger.info("🤖 Using fallback LLM service")
    
    async def answer_legal_question(self, question: str, context_documents: List[Dict], language: str = "en"):
        """Заглушка для ответов на юридические вопросы"""
        logger.warning(f"Fallback LLM called for question: {question[:50]}...")
        
        # Создаем демо ответ
        from services.llm_service import LLMResponse
        
        if language == "uk":
            demo_content = f"""⚠️ ДЕМО РЕЖИМ: Ollama недоступний
            
На основі знайдених документів я би відповів на ваше запитання: "{question}"

📚 Знайдено {len(context_documents)} релевантних документів у базі знань.

💡 Для отримання повноцінних AI-відповідей:
1. Встановіть Ollama: https://ollama.ai
2. Завантажте модель: ollama pull llama3.2
3. Перезапустіть сервер

🔧 Поточний статус: Ollama сервіс недоступний на http://localhost:11434"""
        else:
            demo_content = f"""⚠️ DEMO MODE: Ollama unavailable
            
Based on the found documents, I would answer your question: "{question}"

📚 Found {len(context_documents)} relevant documents in the knowledge base.

💡 To get full AI responses:
1. Install Ollama: https://ollama.ai
2. Pull a model: ollama pull llama3.2
3. Restart the server

🔧 Current status: Ollama service unavailable at http://localhost:11434"""
        
        return LLMResponse(
            content=demo_content,
            model="fallback",
            tokens_used=0,
            response_time=0.1,
            success=False,
            error="Ollama service not available"
        )
    
    async def get_service_status(self):
        """Возвращает статус fallback LLM сервиса"""
        return {
            "ollama_available": False,
            "models_available": [],
            "default_model": "fallback",
            "base_url": "N/A",
            "system_prompts_loaded": 0,
            "supported_languages": ["en", "uk"],
            "error": "Ollama service not available - install Ollama and restart server",
            "service_type": "fallback",
            "recommendations": [
                "Install Ollama from https://ollama.ai",
                "Run: ollama pull llama3.2",
                "Ensure Ollama is running on http://localhost:11434",
                "Restart the Legal Assistant server"
            ]
        }

# ====================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ СЕРВИСОВ
# ====================================

# Глобальные сервисы
document_service: Optional[object] = None
scraper: Optional[object] = None
llm_service: Optional[object] = None  # НОВЫЙ СЕРВИС
SERVICES_AVAILABLE: bool = False
CHROMADB_ENABLED: bool = False
LLM_ENABLED: bool = False  # НОВЫЙ ФЛАГ

async def init_services():
    """Инициализация всех сервисов приложения включая LLM"""
    global document_service, scraper, llm_service, SERVICES_AVAILABLE, CHROMADB_ENABLED, LLM_ENABLED
    
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
    # ИНИЦИАЛИЗАЦИЯ LLM СЕРВИСА
    # ====================================
    try:
        if settings.OLLAMA_ENABLED and not settings.LLM_DEMO_MODE:
            from services.llm_service import create_llm_service
            
            llm_service = create_llm_service(
                ollama_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_DEFAULT_MODEL
            )
            
            # Проверяем доступность Ollama
            status = await llm_service.get_service_status()
            
            if status["ollama_available"]:
                LLM_ENABLED = True
                logger.info("✅ LLM service initialized with Ollama")
                logger.info(f"   Available models: {status['models_available']}")
            else:
                logger.warning(f"⚠️ LLM service created but Ollama unavailable: {status.get('error')}")
                LLM_ENABLED = False
        else:
            logger.info("ℹ️ LLM service disabled in configuration or demo mode")
            LLM_ENABLED = False
            
    except ImportError as e:
        logger.error(f"❌ LLM service import failed: {e}")
        llm_service = None
        LLM_ENABLED = False
    except Exception as e:
        logger.error(f"❌ Error initializing LLM service: {e}")
        llm_service = None
        LLM_ENABLED = False
    
    # ====================================
    # ФИНАЛЬНЫЙ СТАТУС
    # ====================================
    logger.info(f"📊 Services status:")
    logger.info(f"   Document service: {'✅' if document_service else '❌'}")
    logger.info(f"   ChromaDB enabled: {'✅' if CHROMADB_ENABLED else '❌'}")
    logger.info(f"   Scraper service: {'✅' if scraper else '❌'}")
    logger.info(f"   LLM service: {'✅' if LLM_ENABLED else '❌'}")
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

def get_llm_service():
    """Dependency для получения LLM сервиса"""
    if not llm_service or not LLM_ENABLED:
        # Создаем заглушку если LLM недоступен
        logger.debug("Using fallback LLM service")
        return FallbackLLMService()
    return llm_service

def get_services_status():
    """Dependency для получения статуса сервисов"""
    return {
        "document_service_available": document_service is not None,
        "scraper_available": scraper is not None,
        "llm_available": LLM_ENABLED,
        "llm_service_created": llm_service is not None,
        "chromadb_enabled": CHROMADB_ENABLED,
        "services_available": SERVICES_AVAILABLE,
        "fallback_mode": document_service is None or scraper is None or not LLM_ENABLED,
        "ollama_enabled": settings.OLLAMA_ENABLED,
        "llm_demo_mode": settings.LLM_DEMO_MODE
    }

# ====================================
# ДОПОЛНИТЕЛЬНЫЕ UTILITY FUNCTIONS
# ====================================

async def get_system_health():
    """Получает детальную информацию о здоровье системы"""
    status = get_services_status()
    
    # Проверяем статус LLM если он доступен
    llm_status = {}
    if llm_service and LLM_ENABLED:
        try:
            llm_status = await llm_service.get_service_status()
        except Exception as e:
            llm_status = {"error": str(e), "available": False}
    
    health_info = {
        "overall_status": "healthy" if status["services_available"] and status["llm_available"] else "degraded",
        "services": status,
        "llm_status": llm_status,
        "dependencies": {
            "fastapi": True,  # Если мы дошли до сюда, FastAPI работает
            "pydantic": True, # Аналогично для Pydantic
        },
        "features": {
            "document_processing": status["document_service_available"],
            "web_scraping": status["scraper_available"], 
            "vector_search": status["chromadb_enabled"],
            "ai_responses": status["llm_available"],
            "demo_mode": not status["services_available"] or status["llm_demo_mode"]
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
    
    if not status["llm_available"]:
        if not settings.OLLAMA_ENABLED:
            recommendations.append({
                "priority": "high",
                "category": "ai_responses",
                "message": "Enable Ollama in configuration",
                "command": "Set OLLAMA_ENABLED=true in environment or config"
            })
        else:
            recommendations.append({
                "priority": "high",
                "category": "ai_responses", 
                "message": "Install and start Ollama for AI responses",
                "command": "Install from https://ollama.ai, then run: ollama pull llama3.2"
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

async def cleanup_services():
    """Правильно закрывает все сервисы при выключении"""
    global llm_service, scraper
    
    logger.info("🧹 Cleaning up services...")
    
    try:
        if llm_service and hasattr(llm_service, 'close'):
            await llm_service.close()
            logger.info("✅ LLM service closed")
    except Exception as e:
        logger.error(f"Error closing LLM service: {e}")
    
    try:
        if scraper and hasattr(scraper, 'close'):
            await scraper.close()
            logger.info("✅ Scraper service closed")
    except Exception as e:
        logger.error(f"Error closing scraper service: {e}")
    
    logger.info("✅ Services cleanup completed")

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
    "cleanup_services",  # НОВЫЙ ЭКСПОРТ
    "get_document_service", 
    "get_scraper_service",
    "get_llm_service",  # НОВЫЙ ЭКСПОРТ
    "get_services_status",
    "get_system_health",
    "get_service_recommendations",
    "FallbackDocumentService",
    "FallbackScraperService",
    "FallbackLLMService",  # НОВЫЙ ЭКСПОРТ
    "SERVICES_AVAILABLE",
    "CHROMADB_ENABLED",
    "LLM_ENABLED",  # НОВЫЙ ЭКСПОРТ
    "document_service",
    "scraper",
    "llm_service"  # НОВЫЙ ЭКСПОРТ
]