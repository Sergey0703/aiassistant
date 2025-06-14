# ====================================
# ФАЙЛ: backend/api/admin/stats.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для админских endpoints статистики
# ====================================

"""
Admin Stats Endpoints - Админские endpoints для статистики
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
import time
from datetime import datetime, timedelta

from models.responses import AdminStats
from app.dependencies import get_document_service, get_services_status, CHROMADB_ENABLED
from api.user.chat import chat_history

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    document_service = Depends(get_document_service),
    services_status = Depends(get_services_status)
):
    """Статистика для админ панели"""
    try:
        # Базовая статистика
        stats_data = {
            "total_chats": len(chat_history),
            "categories": ["general", "legislation", "jurisprudence", "government", "civil_rights", "scraped"],
            "services_status": services_status
        }
        
        # Статистика документов
        if document_service:
            try:
                vector_stats = await document_service.get_stats()
                stats_data.update({
                    "total_documents": vector_stats.get("total_documents", 0),
                    "database_type": vector_stats.get("database_type", "Unknown"),
                    "vector_db_info": vector_stats
                })
                
                # Обновляем категории реальными данными
                real_categories = vector_stats.get("categories", [])
                if real_categories:
                    stats_data["categories"] = real_categories
                    
            except Exception as e:
                logger.error(f"Error getting vector stats: {e}")
                stats_data.update({
                    "total_documents": 0,
                    "vector_db_error": str(e),
                    "database_type": "Error"
                })
        else:
            stats_data.update({
                "total_documents": 0,
                "database_type": "Unavailable"
            })
        
        return AdminStats(**stats_data)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/stats/detailed")
async def get_detailed_stats(
    document_service = Depends(get_document_service),
    services_status = Depends(get_services_status)
):
    """Детальная статистика для dashboard"""
    try:
        # Базовая статистика
        base_stats = await get_admin_stats(document_service, services_status)
        
        # Анализ чатов
        chat_stats = _analyze_chat_history()
        
        # Анализ документов по категориям
        category_stats = await _analyze_document_categories(document_service)
        
        # Производительность системы
        performance_stats = await _get_performance_stats(document_service)
        
        return {
            "base": base_stats.dict(),
            "chat_analytics": chat_stats,
            "document_analytics": category_stats,
            "performance": performance_stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Detailed stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get detailed stats: {str(e)}")

@router.get("/stats/usage")
async def get_usage_stats():
    """Статистика использования системы"""
    try:
        # Анализ использования за последние 24 часа
        now = time.time()
        day_ago = now - (24 * 60 * 60)
        
        recent_chats = [
            chat for chat in chat_history 
            if chat.get("timestamp", 0) > day_ago
        ]
        
        # Анализ по часам
        hourly_usage = {}
        for chat in recent_chats:
            timestamp = chat.get("timestamp", 0)
            hour = datetime.fromtimestamp(timestamp).hour
            hourly_usage[hour] = hourly_usage.get(hour, 0) + 1
        
        # Анализ языков
        language_usage = {}
        for chat in recent_chats:
            lang = chat.get("language", "unknown")
            language_usage[lang] = language_usage.get(lang, 0) + 1
        
        # Анализ запросов с источниками
        queries_with_sources = len([
            chat for chat in recent_chats 
            if chat.get("sources")
        ])
        
        return {
            "period": "last_24_hours",
            "total_queries": len(recent_chats),
            "queries_with_sources": queries_with_sources,
            "success_rate": (queries_with_sources / len(recent_chats) * 100) if recent_chats else 0,
            "hourly_distribution": hourly_usage,
            "language_distribution": language_usage,
            "average_query_length": sum(len(chat.get("message", "")) for chat in recent_chats) / len(recent_chats) if recent_chats else 0
        }
        
    except Exception as e:
        logger.error(f"Usage stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage stats: {str(e)}")

@router.get("/stats/system")
async def get_system_stats(services_status = Depends(get_services_status)):
    """Системная статистика и статус здоровья"""
    try:
        import psutil
        import platform
        
        # Системная информация
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('.').percent
        }
        
        # Статус сервисов
        service_health = {
            "all_services_healthy": all(services_status.values()),
            "services_detail": services_status,
            "database_type": "ChromaDB" if CHROMADB_ENABLED else "SimpleVectorDB"
        }
        
        # Рекомендации
        recommendations = []
        
        if system_info["memory_percent"] > 80:
            recommendations.append("High memory usage detected. Consider restarting the application.")
        
        if system_info["disk_usage"] > 90:
            recommendations.append("Low disk space. Consider cleaning up old files.")
        
        if not service_health["all_services_healthy"]:
            recommendations.append("Some services are unavailable. Check logs for details.")
        
        return {
            "system": system_info,
            "services": service_health,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        # psutil не установлен
        return {
            "system": {"status": "psutil not installed"},
            "services": services_status,
            "recommendations": ["Install psutil for detailed system monitoring"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"System stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

def _analyze_chat_history():
    """Анализирует историю чатов"""
    if not chat_history:
        return {
            "total_messages": 0,
            "average_length": 0,
            "languages": {},
            "success_rate": 0
        }
    
    total_length = sum(len(chat.get("message", "")) for chat in chat_history)
    languages = {}
    successful_queries = 0
    
    for chat in chat_history:
        # Анализ языков
        lang = chat.get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1
        
        # Успешные запросы (с источниками)
        if chat.get("sources"):
            successful_queries += 1
    
    return {
        "total_messages": len(chat_history),
        "average_length": total_length / len(chat_history),
        "languages": languages,
        "success_rate": (successful_queries / len(chat_history)) * 100
    }

async def _analyze_document_categories(document_service):
    """Анализирует документы по категориям"""
    try:
        if not document_service:
            return {"error": "Document service unavailable"}
        
        stats = await document_service.get_stats()
        categories = stats.get("categories", [])
        
        # Если есть доступ к документам, анализируем их
        category_counts = {}
        
        if CHROMADB_ENABLED:
            try:
                documents = await document_service.get_all_documents()
                for doc in documents:
                    category = doc.get("category", "unknown")
                    category_counts[category] = category_counts.get(category, 0) + 1
            except:
                # Fallback к базовому списку категорий
                for cat in categories:
                    category_counts[cat] = 0
        else:
            # SimpleVectorDB версия
            try:
                import os, json
                db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
                if os.path.exists(db_file):
                    with open(db_file, 'r', encoding='utf-8') as f:
                        documents = json.load(f)
                    
                    for doc in documents:
                        category = doc.get("category", "unknown")
                        category_counts[category] = category_counts.get(category, 0) + 1
            except:
                pass
        
        return {
            "total_categories": len(categories),
            "category_distribution": category_counts,
            "most_popular": max(category_counts, key=category_counts.get) if category_counts else None
        }
        
    except Exception as e:
        logger.error(f"Category analysis error: {e}")
        return {"error": str(e)}

async def _get_performance_stats(document_service):
    """Получает статистику производительности"""
    try:
        start_time = time.time()
        
        # Тестируем поиск
        search_start = time.time()
        try:
            await document_service.search("test query", limit=1)
            search_time = time.time() - search_start
        except:
            search_time = -1
        
        # Тестируем получение статистики
        stats_start = time.time()
        try:
            await document_service.get_stats()
            stats_time = time.time() - stats_start
        except:
            stats_time = -1
        
        total_time = time.time() - start_time
        
        return {
            "search_response_time": search_time,
            "stats_response_time": stats_time,
            "total_test_time": total_time,
            "database_type": "ChromaDB" if CHROMADB_ENABLED else "SimpleVectorDB",
            "performance_rating": "good" if search_time < 1.0 and search_time > 0 else "needs_improvement"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "performance_rating": "unknown"
        }