# ====================================
# ФАЙЛ: backend/api/user/chat.py (ОБНОВЛЕННАЯ ВЕРСИЯ С LLM)
# Заменить существующий файл полностью
# ====================================

"""
User Chat Endpoints - Пользовательские endpoints для чата с AI интеграцией
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging
import time

from models.requests import ChatMessage, ChatHistoryRequest
from models.responses import ChatResponse, ChatHistoryResponse, ChatHistoryItem
from app.dependencies import get_document_service, get_llm_service
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Временное хранение для истории чатов
chat_history: List[Dict[str, Any]] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    message: ChatMessage,
    document_service = Depends(get_document_service),
    llm_service = Depends(get_llm_service)
):
    """Основной endpoint для чата с юридическим ассистентом с AI поддержкой"""
    try:
        search_results = []
        sources = []
        
        # ====================================
        # ЭТАП 1: ПОИСК РЕЛЕВАНТНЫХ ДОКУМЕНТОВ
        # ====================================
        try:
            search_results = await document_service.search(
                query=message.message,
                limit=settings.MAX_CONTEXT_DOCUMENTS,  # Используем конфиг лимит
                min_relevance=0.3  # Минимальный порог релевантности 30%
            )
            
            # Формируем источники только из релевантных документов
            sources = [result.get('filename', 'Unknown') for result in search_results]
            
            logger.info(f"🔍 Found {len(search_results)} relevant documents for query: '{message.message[:50]}...'")
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            search_results = []
        
        # ====================================
        # ЭТАП 2: ГЕНЕРАЦИЯ AI ОТВЕТА
        # ====================================
        ai_response = None
        response_text = ""
        
        if search_results and len(search_results) > 0:
            try:
                logger.info("🤖 Generating AI response based on found documents...")
                
                # Подготавливаем контекст для LLM
                context_documents = []
                for result in search_results:
                    # Ограничиваем длину каждого документа
                    content = result.get('content', '')
                    if len(content) > settings.CONTEXT_TRUNCATE_LENGTH:
                        content = content[:settings.CONTEXT_TRUNCATE_LENGTH] + "..."
                    
                    context_doc = {
                        "filename": result.get('filename', 'Unknown'),
                        "content": content,
                        "relevance_score": result.get('relevance_score', 0.0),
                        "metadata": result.get('metadata', {})
                    }
                    context_documents.append(context_doc)
                
                # Генерируем ответ через LLM
                ai_response = await llm_service.answer_legal_question(
                    question=message.message,
                    context_documents=context_documents,
                    language=message.language
                )
                
                if ai_response.success and ai_response.content.strip():
                    # Используем AI ответ
                    response_text = ai_response.content.strip()
                    
                    logger.info(f"✅ AI response generated: {len(response_text)} chars, "
                              f"{ai_response.tokens_used} tokens, {ai_response.response_time:.2f}s")
                else:
                    # AI не смог ответить, используем fallback
                    logger.warning(f"AI response failed: {ai_response.error}")
                    response_text = _generate_fallback_response_with_context(
                        message.message, search_results, message.language, ai_response.error
                    )
                    
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                # Fallback если AI полностью недоступен
                response_text = _generate_fallback_response_with_context(
                    message.message, search_results, message.language, str(e)
                )
        else:
            # Нет релевантных документов - генерируем ответ об отсутствии информации
            response_text = await _generate_no_context_response(
                message.message, message.language, llm_service
            )
        
        # ====================================
        # ЭТАП 3: СОХРАНЕНИЕ В ИСТОРИЮ
        # ====================================
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
            },
            "ai_stats": {
                "ai_used": ai_response is not None and ai_response.success,
                "model": ai_response.model if ai_response else "fallback",
                "tokens_used": ai_response.tokens_used if ai_response else 0,
                "response_time": ai_response.response_time if ai_response else 0,
                "error": ai_response.error if ai_response and not ai_response.success else None
            }
        }
        chat_history.append(chat_entry)
        
        # Ограничиваем историю последними 100 сообщениями
        if len(chat_history) > 100:
            chat_history.pop(0)
        
        # ====================================
        # ЭТАП 4: ЛОГИРОВАНИЕ РЕЗУЛЬТАТА
        # ====================================
        if ai_response and ai_response.success:
            logger.info(f"💬 Chat response completed with AI: query='{message.message[:30]}...', "
                       f"sources={len(sources)}, model={ai_response.model}")
        else:
            logger.info(f"💬 Chat response completed with fallback: query='{message.message[:30]}...', "
                       f"sources={len(sources)}")
        
        return ChatResponse(
            response=response_text,
            sources=sources if sources else None
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

def _generate_fallback_response_with_context(query: str, search_results: List[Dict], 
                                           language: str, error: str = None) -> str:
    """Генерирует fallback ответ когда AI недоступен, но есть найденный контекст"""
    
    # Формируем контекст из найденных документов с информацией о типе совпадения
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
            if language == "uk":
                match_description = "📍 Точне співпадіння"
            else:
                match_description = "📍 Exact match"
        elif match_type == "semantic":
            if language == "uk":
                match_description = "🔍 Семантичне співпадіння"
            else:
                match_description = "🔍 Semantic match"
        else:
            if language == "uk":
                match_description = f"📊 Релевантність: {relevance:.1%}"
            else:
                match_description = f"📊 Relevance: {relevance:.1%}"
        
        context_snippets.append(f"📄 {filename} ({match_description}): {snippet}")
    
    context = "\n\n".join(context_snippets)
    
    if language == "uk":
        response_text = f"""🔍 Результати пошуку для запитання: "{query}"

📚 Знайдено {len(search_results)} релевантних документів у базі знань:

{context}

⚠️ AI-помічник тимчасово недоступний"""
        
        if error:
            response_text += f" (причина: {error})"
        
        response_text += """.

💡 На основі знайдених документів ви можете:
• Переглянути повний текст документів через адмін панель
• Уточнити запит для кращих результатів  
• Спробувати пошук іншими ключовими словами

🔧 Для адміністратора: перевірте статус Ollama сервісу на http://localhost:11434"""
    else:
        response_text = f"""🔍 Search results for query: "{query}"

📚 Found {len(search_results)} relevant documents in the knowledge base:

{context}

⚠️ AI assistant temporarily unavailable"""
        
        if error:
            response_text += f" (reason: {error})"
            
        response_text += """.

💡 Based on the found documents, you can:
• Review the full document text through the admin panel
• Refine your query for better results
• Try searching with different keywords

🔧 For administrator: check Ollama service status at http://localhost:11434"""
    
    return response_text

async def _generate_no_context_response(query: str, language: str, llm_service) -> str:
    """Генерирует ответ когда не найдено релевантных документов"""
    
    # Пытаемся получить AI ответ даже без контекста (общие знания)
    try:
        ai_response = await llm_service.answer_legal_question(
            question=query,
            context_documents=[],
            language=language
        )
        
        if ai_response.success and ai_response.content.strip():
            # AI смог ответить без контекста
            if language == "uk":
                return f"""🤖 Відповідь на основі загальних знань:

{ai_response.content}

⚠️ Зверніть увагу: ця відповідь базується на загальних знаннях AI, а не на документах у вашій базі знань. Для більш точної інформації рекомендуємо додати релевантні документи через адмін панель."""
            else:
                return f"""🤖 Response based on general knowledge:

{ai_response.content}

⚠️ Note: This response is based on the AI's general knowledge, not on documents in your knowledge base. For more accurate information, we recommend adding relevant documents through the admin panel."""
        
    except Exception as e:
        logger.debug(f"AI general knowledge response failed: {e}")
    
    # Fallback если AI недоступен совсем
    try:
        # Пытаемся получить статистику базы данных
        # (предполагаем что document_service доступен из глобального контекста)
        stats = {"total_documents": "невідомо" if language == "uk" else "unknown"}
    except:
        stats = {"total_documents": "невідомо" if language == "uk" else "unknown"}
    
    if language == "uk":
        response_text = f"""🔍 Результати пошуку для запитання: "{query}"

❌ На жаль, не знайдено релевантних документів у базі знань.

🤖 AI-помічник також тимчасово недоступний для надання загальної відповіді.

🤔 Можливі причини:
• Запитання занадто специфічне або містить терміни, яких немає в документах
• Використовуються синоніми або інша термінологія
• Документи з такою інформацією ще не завантажені в систему
• Ollama сервіс недоступний

💡 Рекомендації:
• Спробуйте переформулювати запит більш загальними термінами
• Використовуйте ключові слова замість цілих речень
• Додайте релевантні документи через панель керування
• Перевірте роботу Ollama на http://localhost:11434

📊 Статистика бази знань:
• Доступно документів: {stats.get('total_documents', 'невідомо')}"""
    else:
        response_text = f"""🔍 Search results for query: "{query}"

❌ Unfortunately, no relevant documents found in the knowledge base.

🤖 AI assistant is also temporarily unavailable to provide a general response.

🤔 Possible reasons:
• The query is too specific or contains terms not present in documents
• Using synonyms or different terminology than in documents
• Relevant documents haven't been uploaded to the system yet
• Ollama service is unavailable

💡 Recommendations:
• Try rephrasing the query with more general terms
• Use keywords instead of full sentences
• Add relevant documents through the admin panel
• Check Ollama service at http://localhost:11434

📊 Knowledge base statistics:
• Available documents: {stats.get('total_documents', 'unknown')}"""
    
    return response_text

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
    """Получить статистику чатов с AI метриками"""
    try:
        # Анализируем языки
        languages = {}
        sources_used = 0
        successful_searches = 0
        total_search_results = 0
        ai_responses = 0
        total_tokens = 0
        total_ai_time = 0.0
        
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
            
            # Анализируем AI статистику
            ai_stats = entry.get("ai_stats", {})
            if ai_stats.get("ai_used", False):
                ai_responses += 1
                total_tokens += ai_stats.get("tokens_used", 0)
                total_ai_time += ai_stats.get("response_time", 0)
        
        return {
            "total_messages": len(chat_history),
            "languages": languages,
            "messages_with_sources": sources_used,
            "successful_searches": successful_searches,
            "success_rate": (successful_searches / len(chat_history) * 100) if chat_history else 0,
            "average_sources_per_message": sources_used / len(chat_history) if chat_history else 0,
            "average_results_per_successful_search": total_search_results / successful_searches if successful_searches > 0 else 0,
            
            # AI статистика
            "ai_responses": ai_responses,
            "ai_usage_rate": (ai_responses / len(chat_history) * 100) if chat_history else 0,
            "total_tokens_used": total_tokens,
            "average_tokens_per_ai_response": total_tokens / ai_responses if ai_responses > 0 else 0,
            "total_ai_time": total_ai_time,
            "average_ai_response_time": total_ai_time / ai_responses if ai_responses > 0 else 0
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

@router.get("/chat/llm-direct-test")
async def test_llm_direct():
    """Прямой тест LLM без контекста для диагностики"""
    try:
        import aiohttp
        import json
        
        logger.info("🧪 Testing direct Ollama API call...")
        
        # Прямой вызов к Ollama API
        payload = {
            "model": "llama3:latest",
            "prompt": "Hello, respond with just 'Working!'",
            "stream": False
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            start_time = time.time()
            
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                end_time = time.time()
                
                if response.status == 200:
                    data = await response.json()
                    content = data.get("response", "No response")
                    
                    return {
                        "test": "direct_ollama_api",
                        "success": True,
                        "response_time": end_time - start_time,
                        "status_code": response.status,
                        "response_content": content,
                        "payload_sent": payload
                    }
                else:
                    error_text = await response.text()
                    return {
                        "test": "direct_ollama_api", 
                        "success": False,
                        "response_time": end_time - start_time,
                        "status_code": response.status,
                        "error": error_text
                    }
                    
    except Exception as e:
        return {
            "test": "direct_ollama_api",
            "success": False,
            "error": str(e),
            "recommendation": "Check if Ollama is running on http://localhost:11434"
        }
async def test_llm_functionality(
    question: str = "What is law?",
    language: str = "en",
    llm_service = Depends(get_llm_service)
):
    """Тестовый endpoint для проверки LLM"""
    try:
        logger.info(f"Testing LLM with question: '{question}', language: {language}")
        
        # Тестируем LLM без контекста
        ai_response = await llm_service.answer_legal_question(
            question=question,
            context_documents=[],
            language=language
        )
        
        # Получаем статус сервиса
        service_status = await llm_service.get_service_status()
        
        return {
            "test_successful": ai_response.success,
            "question": question,
            "language": language,
            "ai_response": {
                "content": ai_response.content,
                "model": ai_response.model,
                "tokens_used": ai_response.tokens_used,
                "response_time": ai_response.response_time,
                "success": ai_response.success,
                "error": ai_response.error
            },
            "service_status": service_status
        }
        
    except Exception as e:
        logger.error(f"LLM test error: {e}")
        return {
            "test_successful": False,
            "question": question,
            "error": str(e)
        }