from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import uvicorn
import tempfile
import os
import asyncio
import json
import time
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импорты наших сервисов
try:
    import sys
    import os
    
    # Добавляем текущую папку в Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    
    from services.scraper_service import LegalSiteScraper, ScrapedDocument, UKRAINE_LEGAL_URLS, IRELAND_LEGAL_URLS
    from services.document_processor import DocumentService
    SERVICES_AVAILABLE = True
    logger.info("✅ Services imported successfully")
except ImportError as e:
    logger.error(f"❌ Services import failed: {e}")
    logger.error("Creating fallback services...")
    SERVICES_AVAILABLE = False
    
    # Создаем fallback классы
    class FallbackScraper:
        async def scrape_legal_site(self, url):
            raise Exception("Scraper service unavailable")
        async def scrape_multiple_urls(self, urls, delay=1.0):
            raise Exception("Scraper service unavailable")
    
    class FallbackDocumentService:
        async def process_and_store_file(self, file_path, category):
            raise Exception("Document service unavailable")
        async def search(self, query, category=None, limit=5):
            return []
        async def get_stats(self):
            return {"total_documents": 0, "error": "Service unavailable"}
    
    LegalSiteScraper = FallbackScraper
    DocumentService = FallbackDocumentService
    UKRAINE_LEGAL_URLS = []
    IRELAND_LEGAL_URLS = []

app = FastAPI(title="Legal Assistant API", version="2.0.0", description="AI Legal Assistant with document scraping and ChromaDB")

# CORS настройка
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация сервисов
if SERVICES_AVAILABLE:
    try:
        document_service = DocumentService()
        scraper = LegalSiteScraper()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        document_service = None
        scraper = None
else:
    document_service = None
    scraper = None

# === МОДЕЛИ ДАННЫХ ===

class ChatMessage(BaseModel):
    message: str
    language: str = "en"

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None

class DocumentUpload(BaseModel):
    filename: str
    content: str
    category: Optional[str] = None

class URLScrapeRequest(BaseModel):
    url: HttpUrl
    category: Optional[str] = "scraped"
    selectors: Optional[Dict[str, str]] = None

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 5

class BulkScrapeRequest(BaseModel):
    urls: List[str]
    category: str = "scraped"
    delay: float = 1.0

# Временное хранение для истории чатов
chat_history: List[Dict[str, Any]] = []

# === БАЗОВЫЕ ENDPOINTS ===

@app.get("/")
async def root():
    return {
        "message": "Legal Assistant API v2.0 with scraping and ChromaDB",
        "version": "2.0.0",
        "services_available": SERVICES_AVAILABLE,
        "features": [
            "Document Upload & Processing",
            "Website Scraping",
            "Vector Search with ChromaDB",
            "Multi-language Support",
            "Legal Document Analysis"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Проверка состояния системы"""
    health_status = {
        "status": "healthy",
        "services": {
            "document_service": document_service is not None,
            "scraper": scraper is not None,
            "services_module": SERVICES_AVAILABLE
        }
    }
    
    if document_service:
        try:
            stats = await document_service.get_stats()
            health_status["vector_db"] = stats
        except Exception as e:
            health_status["vector_db_error"] = str(e)
    
    return health_status

# === USER ENDPOINTS ===

@app.post("/api/user/chat", response_model=ChatResponse)
async def chat_with_assistant(message: ChatMessage):
    """Основной endpoint для чата с юридическим ассистентом"""
    try:
        search_results = []
        sources = []
        
        # Поиск релевантных документов если доступен document_service
        if document_service:
            try:
                search_results = await document_service.search(
                    query=message.message,
                    limit=3
                )
                
                # Формируем источники
                sources = [result['filename'] for result in search_results]
                
            except Exception as e:
                logger.error(f"Search error: {e}")
        
        # Формируем ответ на основе найденных документов
        if search_results and len(search_results) > 0:
            # Создаем контекст из найденных документов
            context_snippets = []
            for result in search_results:
                snippet = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                context_snippets.append(f"📄 {result['filename']}: {snippet}")
            
            context = "\n\n".join(context_snippets)
            
            if message.language == "uk":
                response_text = f"""На основі знайдених документів у базі знань:

🤖 Відповідь: Знайдено релевантні документи для вашого запитання: "{message.message}"

📚 Релевантний контекст:
{context}

💡 Примітка: У повній версії з LLaMA тут буде детальна відповідь на основі цього контексту."""
            else:
                response_text = f"""Based on documents found in the knowledge base:

🤖 Answer: Found relevant documents for your question: "{message.message}"

📚 Relevant context:
{context}

💡 Note: In the full version with LLaMA, this will be a detailed answer based on this context."""
        else:
            # Нет релевантных документов
            if message.language == "uk":
                response_text = f"""Дякую за ваше питання: "{message.message}"

🔍 На жаль, не знайдено релевантних документів у базі знань.

💡 Рекомендації:
• Спробуйте переформулювати запит
• Додайте більше документів через админ-панель
• Використайте парсер сайтів для збагачення бази знань

📊 Поточний стан системи: {"ChromaDB активна" if document_service else "ChromaDB недоступна"}"""
            else:
                response_text = f"""Thank you for your question: "{message.message}"

🔍 Unfortunately, no relevant documents found in the knowledge base.

💡 Recommendations:
• Try rephrasing your query
• Add more documents through the admin panel
• Use the website scraper to enrich the knowledge base

📊 Current system status: {"ChromaDB active" if document_service else "ChromaDB unavailable"}"""
        
        # Сохраняем в историю
        chat_entry = {
            "message": message.message,
            "response": response_text,
            "language": message.language,
            "sources": sources,
            "timestamp": asyncio.get_event_loop().time()
        }
        chat_history.append(chat_entry)
        
        # Ограничиваем историю последними 100 сообщениями
        if len(chat_history) > 100:
            chat_history.pop(0)
        
        return ChatResponse(
            response=response_text,
            sources=sources if sources else None
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

@app.get("/api/user/chat/history")
async def get_chat_history():
    """Получить историю чата"""
    return {
        "history": chat_history[-10:],  # Последние 10 сообщений
        "total_messages": len(chat_history)
    }

@app.post("/api/user/search")
async def search_documents(search_request: SearchRequest):
    """Поиск по документам"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service unavailable")
    
    try:
        results = await document_service.search(
            query=search_request.query,
            category=search_request.category,
            limit=search_request.limit
        )
        
        return {
            "query": search_request.query,
            "results": results,
            "total_found": len(results),
            "search_metadata": {
                "category_filter": search_request.category,
                "limit": search_request.limit
            }
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# === ADMIN ENDPOINTS ===

@app.post("/api/admin/documents/upload")
async def upload_document_file(file: UploadFile = File(...), category: str = Form("general")):
    """Загрузка документа через файл"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service unavailable")
    
    try:
        # Проверяем размер файла (макс 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        # Сохраняем временный файл
        file_extension = Path(file.filename or "document.txt").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Обрабатываем и сохраняем в векторную базу
            success = await document_service.process_and_store_file(tmp_file_path, category)
            
            if success:
                return {
                    "message": "Document uploaded and processed successfully",
                    "filename": file.filename,
                    "category": category,
                    "size": len(content),
                    "file_type": file.content_type
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to process document")
                
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.post("/api/admin/documents/upload-text")
async def upload_text_document(document: DocumentUpload):
    """Загрузка документа через текст"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service unavailable")
    
    try:
        # Создаем временный файл с текстом
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
            tmp_file.write(document.content)
            tmp_file_path = tmp_file.name
        
        try:
            # Обрабатываем и сохраняем
            success = await document_service.process_and_store_file(
                tmp_file_path, 
                document.category or "general"
            )
            
            if success:
                return {
                    "message": "Document uploaded and processed successfully",
                    "filename": document.filename,
                    "category": document.category or "general",
                    "content_length": len(document.content)
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to process document")
                
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Text upload error: {str(e)}")

@app.post("/api/admin/scrape/url")
async def scrape_single_url(scrape_request: URLScrapeRequest):
    """Парсинг одного URL и сохранение в базу документов"""
    if not scraper or not document_service:
        raise HTTPException(status_code=503, detail="Scraping services unavailable")
    
    try:
        # Парсим URL
        document = await scraper.scrape_legal_site(str(scrape_request.url))
        
        if not document:
            raise HTTPException(status_code=400, detail="Failed to scrape URL - no content extracted")
        
        # Проверяем минимальную длину контента
        if len(document.content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Scraped content too short")
        
        # Создаем временный файл с контентом
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
            tmp_file.write(document.content)
            tmp_file_path = tmp_file.name
        
        try:
            # Обрабатываем и сохраняем в векторную базу
            success = await document_service.process_and_store_file(
                tmp_file_path, 
                scrape_request.category
            )
            
            if success:
                return {
                    "message": "URL scraped and processed successfully",
                    "url": str(scrape_request.url),
                    "title": document.title,
                    "category": scrape_request.category,
                    "content_length": len(document.content),
                    "metadata": document.metadata
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to process scraped content")
                
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")

@app.post("/api/admin/scrape/bulk")
async def scrape_multiple_urls(bulk_request: BulkScrapeRequest):
    """Парсинг нескольких URL"""
    if not scraper or not document_service:
        raise HTTPException(status_code=503, detail="Scraping services unavailable")
    
    try:
        # Ограничиваем количество URL
        if len(bulk_request.urls) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 URLs allowed per request")
        
        # Фильтруем валидные URL
        valid_urls = [url.strip() for url in bulk_request.urls if url.strip()]
        
        if not valid_urls:
            raise HTTPException(status_code=400, detail="No valid URLs provided")
        
        logger.info(f"Starting bulk scrape of {len(valid_urls)} URLs")
        
        # Парсим URL
        documents = await scraper.scrape_multiple_urls(valid_urls, bulk_request.delay)
        
        results = []
        successful = 0
        
        for i, document in enumerate(documents):
            result = {
                "url": valid_urls[i] if i < len(valid_urls) else "unknown",
                "title": document.title if document else "Failed",
                "success": False,
                "content_length": 0,
                "error": None
            }
            
            if document and len(document.content.strip()) >= 50:
                # Создаем временный файл
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
                    tmp_file.write(document.content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Обрабатываем документ
                    success = await document_service.process_and_store_file(tmp_file_path, bulk_request.category)
                    
                    result.update({
                        "success": success,
                        "content_length": len(document.content),
                        "title": document.title
                    })
                    
                    if success:
                        successful += 1
                    else:
                        result["error"] = "Processing failed"
                        
                except Exception as e:
                    result["error"] = str(e)
                finally:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
            else:
                result["error"] = "No content or content too short"
            
            results.append(result)
        
        return {
            "message": f"Processed {successful}/{len(results)} URLs successfully",
            "results": results,
            "summary": {
                "total_processed": len(results),
                "successful": successful,
                "failed": len(results) - successful,
                "category": bulk_request.category
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk scrape error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk scraping error: {str(e)}")

@app.get("/api/admin/documents")
async def get_documents():
    """Получить детальный список всех документов"""
    if not document_service:
        return {
            "message": "Document service unavailable",
            "documents": [],
            "total": 0
        }
    
    try:
        # Получаем документы из простой базы данных
        db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
        
        if not os.path.exists(db_file):
            return {
                "documents": [],
                "total": 0,
                "message": "No documents database found"
            }
        
        with open(db_file, 'r', encoding='utf-8') as f:
            raw_documents = json.load(f)
        
        # Форматируем документы для frontend
        formatted_documents = []
        for doc in raw_documents:
            # Определяем источник по метаданным или URL
            source = "Unknown"
            if "scraped_at" in doc.get("metadata", {}):
                source = "Web Scraping"
            elif doc.get("category") == "ukraine_legal":
                source = "Ukraine Legal Sites"
            elif doc.get("category") == "ireland_legal":
                source = "Ireland Legal Sites"
            elif doc.get("category") == "scraped":
                source = "Manual URL Scraping"
            elif "file_extension" in doc.get("metadata", {}):
                source = "File Upload"
            
            # Извлекаем URL если есть
            original_url = "N/A"
            if doc.get("metadata", {}).get("scraped_at"):
                # Пытаемся найти URL в контенте
                content = doc.get("content", "")
                if "URL:" in content:
                    url_line = [line for line in content.split('\n') if line.startswith('URL:')]
                    if url_line:
                        original_url = url_line[0].replace('URL:', '').strip()
            
            formatted_doc = {
                "id": doc["id"],
                "filename": doc["filename"],
                "category": doc["category"],
                "source": source,
                "original_url": original_url,
                "content": doc["content"],
                "size": doc["metadata"].get("content_length", len(doc["content"])),
                "word_count": doc["metadata"].get("word_count", 0),
                "chunks_count": len(doc.get("chunks", [])),
                "added_at": doc.get("added_at", time.time()),
                "metadata": doc["metadata"]
            }
            formatted_documents.append(formatted_doc)
        
        # Сортируем по времени добавления (новые первые)
        formatted_documents.sort(key=lambda x: x["added_at"], reverse=True)
        
        return {
            "documents": formatted_documents,
            "total": len(formatted_documents),
            "message": f"Found {len(formatted_documents)} documents"
        }
        
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return {
            "documents": [],
            "total": 0,
            "error": str(e)
        }

@app.delete("/api/admin/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Удалить документ"""
    if not document_service:
        raise HTTPException(status_code=503, detail="Document service unavailable")
    
    try:
        # URL decode ID
        import urllib.parse
        decoded_id = urllib.parse.unquote(doc_id)
        logger.info(f"Attempting to delete document with ID: {decoded_id}")
        
        # Для простой базы данных - удаляем из JSON файла
        db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
        
        if not os.path.exists(db_file):
            raise HTTPException(status_code=404, detail="Database not found")
        
        with open(db_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        # Ищем документ для удаления
        original_count = len(documents)
        found_doc = None
        
        # Поиск по точному совпадению ID
        for doc in documents:
            if doc['id'] == decoded_id:
                found_doc = doc
                break
        
        if not found_doc:
            logger.warning(f"Document not found with ID: {decoded_id}")
            logger.info(f"Available document IDs: {[doc['id'] for doc in documents[:3]]}")
            raise HTTPException(status_code=404, detail=f"Document with ID '{decoded_id}' not found")
        
        # Удаляем найденный документ
        documents = [doc for doc in documents if doc['id'] != decoded_id]
        
        # Сохраняем обновленный список
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        deleted_count = original_count - len(documents)
        logger.info(f"Successfully deleted document: {found_doc['filename']}")
        
        return {
            "message": f"Document '{found_doc['filename']}' deleted successfully", 
            "deleted_count": deleted_count,
            "deleted_id": decoded_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Статистика для админ панели"""
    try:
        stats = {
            "total_chats": len(chat_history),
            "categories": ["general", "legislation", "jurisprudence", "government", "civil_rights", "scraped"],
            "services_status": {
                "document_service": document_service is not None,
                "scraper": scraper is not None,
                "services_available": SERVICES_AVAILABLE
            }
        }
        
        if document_service:
            try:
                vector_stats = await document_service.get_stats()
                stats.update({
                    "total_documents": vector_stats["total_documents"],
                    "vector_db_info": vector_stats
                })
            except Exception as e:
                stats.update({
                    "total_documents": 0,
                    "vector_db_error": str(e)
                })
        else:
            stats["total_documents"] = 0
            
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ПРЕДУСТАНОВЛЕННЫЕ САЙТЫ ===

@app.get("/api/admin/predefined-sites")
async def get_predefined_sites():
    """Получить список предустановленных юридических сайтов"""
    if not SERVICES_AVAILABLE:
        return {
            "ukraine": [],
            "ireland": [],
            "error": "Services not available"
        }
    
    return {
        "ukraine": UKRAINE_LEGAL_URLS,
        "ireland": IRELAND_LEGAL_URLS,
        "total": {
            "ukraine": len(UKRAINE_LEGAL_URLS),
            "ireland": len(IRELAND_LEGAL_URLS)
        }
    }

@app.post("/api/admin/scrape/predefined")
async def scrape_predefined_sites(country: str = "ukraine", limit: int = 5):
    """Парсинг предустановленных сайтов"""
    if not scraper or not document_service:
        raise HTTPException(status_code=503, detail="Scraping services unavailable")
    
    try:
        if country == "ukraine":
            urls = UKRAINE_LEGAL_URLS[:limit]
            category = "ukraine_legal"
        elif country == "ireland":
            urls = IRELAND_LEGAL_URLS[:limit]
            category = "ireland_legal"
        else:
            raise HTTPException(status_code=400, detail="Supported countries: ukraine, ireland")
        
        if not urls:
            raise HTTPException(status_code=400, detail=f"No predefined URLs for {country}")
        
        # Используем bulk scraping с увеличенной задержкой для уважения к серверам
        bulk_request = BulkScrapeRequest(
            urls=urls,
            category=category,
            delay=2.0
        )
        
        return await scrape_multiple_urls(bulk_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predefined scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS ===

@app.get("/api/system/info")
async def get_system_info():
    """Информация о системе"""
    return {
        "app_name": "Legal Assistant API",
        "version": "2.0.0",
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "services": {
            "document_processing": document_service is not None,
            "web_scraping": scraper is not None,
            "vector_search": document_service is not None
        },
        "supported_formats": ["PDF", "DOCX", "TXT", "MD", "HTML"] if document_service else [],
        "supported_countries": ["Ukraine", "Ireland"] if scraper else []
    }

@app.post("/api/admin/clear-history")
async def clear_chat_history():
    """Очистить историю чатов"""
    global chat_history
    old_count = len(chat_history)
    chat_history.clear()
    
    return {
        "message": f"Cleared {old_count} chat messages",
        "remaining": len(chat_history)
    }

# === STARTUP/SHUTDOWN EVENTS ===

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("🚀 Legal Assistant API starting up...")
    logger.info(f"Services available: {SERVICES_AVAILABLE}")
    if document_service:
        logger.info("✅ Document service initialized")
    if scraper:
        logger.info("✅ Web scraper initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    logger.info("🛑 Legal Assistant API shutting down...")

# === MAIN ===

if __name__ == "__main__":
    print("🏛️ Legal Assistant API v2.0")
    print("📚 Features: Document Processing, Web Scraping, Vector Search")
    print("🌐 Starting server on http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("-" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=False  # Отключаем reload для стабильности
    )