# ====================================
# ФАЙЛ: backend/api/user/search.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для пользовательских endpoints поиска
# ====================================

"""
User Search Endpoints - Пользовательские endpoints для поиска
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
import time

from models.requests import SearchRequest
from models.responses import SearchResponse, SearchResult
from app.dependencies import get_document_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    document_service = Depends(get_document_service)
):
    """Поиск по документам для пользователей"""
    try:
        logger.info(f"Search request: '{search_request.query}' in category '{search_request.category}'")
        
        # Выполняем поиск
        results = await document_service.search(
            query=search_request.query,
            category=search_request.category,
            limit=search_request.limit
        )
        
        # Преобразуем результаты в нужный формат
        formatted_results = []
        for result in results:
            search_result = SearchResult(
                content=result.get('content', ''),
                filename=result.get('filename', 'Unknown'),
                document_id=str(result.get('document_id', '')),
                relevance_score=float(result.get('relevance_score', 0.0)),
                metadata=result.get('metadata', {})
            )
            formatted_results.append(search_result)
        
        # Метаданные поиска
        search_metadata = {
            "category_filter": search_request.category,
            "limit": search_request.limit,
            "execution_time": "fast",  # Можно добавить реальное измерение времени
            "search_type": "semantic" if hasattr(document_service, 'vector_db') else "text"
        }
        
        logger.info(f"Search completed: found {len(formatted_results)} results")
        
        return SearchResponse(
            query=search_request.query,
            results=formatted_results,
            total_found=len(formatted_results),
            search_metadata=search_metadata
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/search/suggestions")
async def get_search_suggestions(
    query: str,
    limit: int = 5,
    document_service = Depends(get_document_service)
):
    """Получить предложения для поиска"""
    try:
        if len(query) < 2:
            return {"suggestions": []}
        
        # Простые предложения на основе частых юридических терминов
        legal_terms = [
            "права человека", "human rights",
            "трудовое право", "labor law",
            "гражданское право", "civil law",
            "уголовное право", "criminal law",
            "налоговое право", "tax law",
            "семейное право", "family law",
            "административное право", "administrative law",
            "корпоративное право", "corporate law",
            "недвижимость", "real estate",
            "конституция", "constitution",
            "законодательство", "legislation",
            "судебная практика", "jurisprudence"
        ]
        
        # Фильтруем термины, содержащие часть запроса
        suggestions = [
            term for term in legal_terms 
            if query.lower() in term.lower()
        ][:limit]
        
        return {
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/search/categories")
async def get_search_categories(document_service = Depends(get_document_service)):
    """Получить доступные категории для поиска"""
    try:
        # Получаем статистику и извлекаем категории
        stats = await document_service.get_stats()
        categories = stats.get('categories', [])
        
        # Добавляем описания категорий
        category_descriptions = {
            "general": "Общие документы",
            "legislation": "Законодательство",
            "jurisprudence": "Судебная практика",
            "government": "Государственные документы",
            "civil_rights": "Гражданские права",
            "scraped": "Парсированные документы",
            "ukraine_legal": "Украинское право",
            "ireland_legal": "Ирландское право",
            "civil": "Гражданское право",
            "criminal": "Уголовное право",
            "tax": "Налоговое право",
            "corporate": "Корпоративное право",
            "family": "Семейное право",
            "labor": "Трудовое право",
            "real_estate": "Недвижимость"
        }
        
        # Формируем ответ с описаниями
        formatted_categories = []
        for category in categories:
            formatted_categories.append({
                "id": category,
                "name": category_descriptions.get(category, category.title()),
                "description": category_descriptions.get(category, f"Документы категории {category}")
            })
        
        return {
            "categories": formatted_categories,
            "total": len(formatted_categories)
        }
        
    except Exception as e:
        logger.error(f"Categories error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/search/stats")
async def get_search_stats(document_service = Depends(get_document_service)):
    """Получить статистику поиска"""
    try:
        # Получаем общую статистику документов
        stats = await document_service.get_stats()
        
        return {
            "total_documents": stats.get('total_documents', 0),
            "categories": len(stats.get('categories', [])),
            "database_type": stats.get('database_type', 'Unknown'),
            "search_features": {
                "semantic_search": "ChromaDB" in str(stats.get('database_type', '')),
                "category_filtering": True,
                "metadata_search": True,
                "full_text_search": True
            }
        }
        
    except Exception as e:
        logger.error(f"Search stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get search stats: {str(e)}")