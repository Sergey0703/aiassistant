# ====================================
# ФАЙЛ: backend/api/user/chat.py (ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
User Chat Endpoints - Пользовательские endpoints для чата
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging
import time

from models.requests import ChatMessage, ChatHistoryRequest
from models.responses import ChatResponse, ChatHistoryResponse, ChatHistoryItem
from app.dependencies import get_document_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Временное хранение для истории чатов
chat_history: List[Dict[str, Any]] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    message: ChatMessage,
    document_service = Depends(get_document_service)
):
    """Основной endpoint для чата с юридическим ассистентом"""
    try:
        search_results = []
        sources = []
        
        # Поиск релевантных документов с улучшенной фильтрацией
        try:
            search_results = await document_service.search(
                query=message.message,
                limit=3,
                min_relevance=0.3  # Минимальный порог релевантности 30%
            )
            
            # Формируем источники только из релевантных документов
            sources = [result.get('filename', 'Unknown') for result in search_results]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        # Формируем ответ на основе найденных документов
        if search_results and len(search_results) > 0:
            # Создаем контекст из найденных документов с информацией о типе совпадения
            context_snippets = []
            for result in search_results:
                content = result.get('content', '')
                snippet = content[:300] + "..." if len(content) > 300 else content
                filename = result.get('filename', 'Unknown')
                
                # Показываем тип совпадения
                match_type = result.get('search_info', {}).get('match_type', 'unknown')
                relevance = result.get('relevance_score', 0.0)
                
                # Формируем описание совпадения
                if match_type == "exact":
                    if message.language == "uk":
                        match_description = "📍 Точне співпадіння"
                    else:
                        match_description = "📍 Exact match"
                elif match_type == "semantic":
                    if message.language == "uk":
                        match_description = "🔍 Семантичне співпадіння"
                    else:
                        match_description = "🔍 Semantic match"
                else:
                    if message.language == "uk":
                        match_description = f"📊 Релевантність: {relevance:.1%}"
                    else:
                        match_description = f"📊 Relevance: {relevance:.1%}"
                
                context_snippets.append(f"📄 {filename} ({match_description}): {snippet}")
            
            context = "\n\n".join(context_snippets)
            
            if message.language == "uk":
                response_text = f"""На основі знайдених документів у базі знань:

🤖 Відповідь: Знайдено {len(search_results)} релевантних документів для вашого запитання: "{message.message}"

📚 Релевантний контекст:
{context}

💡 Примітка: У повній версії з LLaMA тут буде детальна відповідь на основі цього контексту."""
            else:
                response_text = f"""Based on documents found in the knowledge base:

🤖 Answer: Found {len(search_results)} relevant documents for your question: "{message.message}"

📚 Relevant context:
{context}

💡 Note: In the full version with LLaMA, this will be a detailed answer based on this context."""
        else:
            # Улучшенный ответ когда ничего релевантного не найдено
            try:
                # Пытаемся получить статистику базы данных
                stats = await document_service.get_stats()
                total_docs = stats.get('total_documents', 'невідомо' if message.language == "uk" else 'unknown')
            except:
                total_docs = 'невідомо' if message.language == "uk" else 'unknown'
            
            if message.language == "uk":
                response_text = f"""🔍 Результати пошуку для запитання: "{message.message}"

❌ На жаль, не знайдено релевантних документів у базі знань.

🤔 Можливі причини:
• Запитання занадто специфічне або містить терміни, яких немає в документах
• Використовуються синоніми або інша термінологія
• Документи з такою інформацією ще не завантажені в систему

💡 Рекомендації для покращення результатів:
• Спробуйте переформулювати запит більш загальними термінами
• Використовуйте ключові слова замість цілих речень
• Перевірте правопис і спробуйте інші варіанти написання
• Спробуйте пошук англійською мовою, якщо документи англомовні

📊 Статистика бази знань:
• Доступно документів: {total_docs}
• Мінімальний поріг релевантності: 30%

🔧 Для адміністратора:
• Додайте більше документів через панель керування
• Використайте парсер сайтів для збагачення бази знань
• Перевірте налаштування категорій документів"""
            else:
                response_text = f"""🔍 Search results for query: "{message.message}"

❌ Unfortunately, no relevant documents found in the knowledge base.

🤔 Possible reasons:
• The query is too specific or contains terms not present in documents
• Using synonyms or different terminology than in documents
• Relevant documents haven't been uploaded to the system yet

💡 Recommendations to improve results:
• Try rephrasing the query with more general terms
• Use keywords instead of full sentences
• Check spelling and try alternative word forms
• Try searching in Ukrainian if documents are in Ukrainian

📊 Knowledge base statistics:
• Available documents: {total_docs}
• Minimum relevance threshold: 30%

🔧 For administrator:
• Add more documents through the admin panel
• Use the website scraper to enrich the knowledge base
• Check document category settings"""
        
        # Сохраняем в историю
        chat_entry = {
            "message": message.message,
            "response": response_text,
            "language": message.language,
            "sources": sources,
            "timestamp": time.time(),
            "search_stats": {
                "found_documents": len(search_results),
                "has_relevant_results": len(search_results) > 0,
                "search_query": message.message
            }
        }
        chat_history.append(chat_entry)
        
        # Ограничиваем историю последними 100 сообщениями
        if len(chat_history) > 100:
            chat_history.pop(0)
        
        # Логируем результат поиска
        if search_results:
            logger.info(f"Chat response generated for query: '{message.message[:50]}...', found {len(search_results)} relevant results")
        else:
            logger.info(f"Chat response generated for query: '{message.message[:50]}...', no relevant results found")
        
        return ChatResponse(
            response=response_text,
            sources=sources if sources else None
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(request: ChatHistoryRequest = ChatHistoryRequest()):
    """Получить историю чата"""
    try:
        # Получаем последние N сообщений
        recent_history = chat_history[-request.limit:] if chat_history else []
        
        # Преобразуем в нужный формат
        formatted_history = []
        for entry in recent_history:
            formatted_entry = ChatHistoryItem(
                message=entry["message"],
                response=entry["response"],
                language=entry["language"],
                sources=entry.get("sources"),
                timestamp=entry.get("timestamp")
            )
            formatted_history.append(formatted_entry)
        
        return ChatHistoryResponse(
            history=formatted_history,
            total_messages=len(chat_history)
        )
        
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@router.delete("/chat/history")
async def clear_chat_history():
    """Очистить историю чатов"""
    try:
        global chat_history
        old_count = len(chat_history)
        chat_history.clear()
        
        logger.info(f"Chat history cleared: {old_count} messages removed")
        
        return {
            "message": f"Cleared {old_count} chat messages",
            "remaining": len(chat_history)
        }
        
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")

@router.get("/chat/stats")
async def get_chat_stats():
    """Получить статистику чатов"""
    try:
        # Анализируем языки
        languages = {}
        sources_used = 0
        successful_searches = 0
        total_search_results = 0
        
        for entry in chat_history:
            lang = entry.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
            
            if entry.get("sources"):
                sources_used += 1
            
            # Анализируем статистику поиска
            search_stats = entry.get("search_stats", {})
            if search_stats.get("has_relevant_results", False):
                successful_searches += 1
                total_search_results += search_stats.get("found_documents", 0)
        
        return {
            "total_messages": len(chat_history),
            "languages": languages,
            "messages_with_sources": sources_used,
            "successful_searches": successful_searches,
            "success_rate": (successful_searches / len(chat_history) * 100) if chat_history else 0,
            "average_sources_per_message": sources_used / len(chat_history) if chat_history else 0,
            "average_results_per_successful_search": total_search_results / successful_searches if successful_searches > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Chat stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat stats: {str(e)}")

@router.get("/chat/search-test")
async def test_search_functionality(
    query: str = "test",
    min_relevance: float = 0.3,
    document_service = Depends(get_document_service)
):
    """Тестовый endpoint для проверки поиска"""
    try:
        logger.info(f"Testing search with query: '{query}', min_relevance: {min_relevance}")
        
        # Выполняем поиск
        results = await document_service.search(
            query=query,
            limit=5,
            min_relevance=min_relevance
        )
        
        # Получаем статистику базы
        try:
            stats = await document_service.get_stats()
        except:
            stats = {"error": "Could not get stats"}
        
        # Формируем детальный ответ
        test_result = {
            "query": query,
            "min_relevance_threshold": min_relevance,
            "found_results": len(results),
            "database_stats": stats,
            "results_details": []
        }
        
        for result in results:
            result_detail = {
                "filename": result.get('filename', 'Unknown'),
                "relevance_score": result.get('relevance_score', 0.0),
                "match_type": result.get('search_info', {}).get('match_type', 'unknown'),
                "confidence": result.get('search_info', {}).get('confidence', 'unknown'),
                "content_preview": result.get('content', '')[:100] + "..." if result.get('content') else "No content"
            }
            test_result["results_details"].append(result_detail)
        
        return {
            "test_successful": True,
            "message": f"Search test completed for query '{query}'",
            "test_result": test_result
        }
        
    except Exception as e:
        logger.error(f"Search test error: {e}")
        return {
            "test_successful": False,
            "message": f"Search test failed for query '{query}'",
            "error": str(e)
        }