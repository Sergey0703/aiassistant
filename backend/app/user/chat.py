# ====================================
# ФАЙЛ: backend/api/user/chat.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для пользовательских endpoints чата
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
from app.dependencies import get_document_service, get_services_status

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
        
        # Поиск релевантных документов
        try:
            search_results = await document_service.search(
                query=message.message,
                limit=3
            )
            
            # Формируем источники
            sources = [result.get('filename', 'Unknown') for result in search_results]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        # Формируем ответ на основе найденных документов
        if search_results and len(search_results) > 0:
            # Создаем контекст из найденных документов
            context_snippets = []
            for result in search_results:
                content = result.get('content', '')
                snippet = content[:300] + "..." if len(content) > 300 else content
                filename = result.get('filename', 'Unknown')
                context_snippets.append(f"📄 {filename}: {snippet}")
            
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

📊 Система готова допомогти вам з юридичними питаннями!"""
            else:
                response_text = f"""Thank you for your question: "{message.message}"

🔍 Unfortunately, no relevant documents found in the knowledge base.

💡 Recommendations:
• Try rephrasing your query
• Add more documents through the admin panel
• Use the website scraper to enrich the knowledge base

📊 The system is ready to help you with legal questions!"""
        
        # Сохраняем в историю
        chat_entry = {
            "message": message.message,
            "response": response_text,
            "language": message.language,
            "sources": sources,
            "timestamp": time.time()
        }
        chat_history.append(chat_entry)
        
        # Ограничиваем историю последними 100 сообщениями
        if len(chat_history) > 100:
            chat_history.pop(0)
        
        logger.info(f"Chat response generated for query: {message.message[:50]}...")
        
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
        
        for entry in chat_history:
            lang = entry.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
            
            if entry.get("sources"):
                sources_used += 1
        
        return {
            "total_messages": len(chat_history),
            "languages": languages,
            "messages_with_sources": sources_used,
            "average_sources_per_message": sources_used / len(chat_history) if chat_history else 0
        }
        
    except Exception as e:
        logger.error(f"Chat stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat stats: {str(e)}")