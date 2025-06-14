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

@router.get("/debug/chromadb-search")
async def debug_chromadb_search(
    query: str = "Statutory Rules",
    document_service = Depends(get_document_service)
):
    """Диагностический endpoint для отладки ChromaDB поиска"""
    try:
        logger.info(f"🔍 Debug ChromaDB search for: {query}")
        
        # Получаем прямой доступ к ChromaDB
        chroma_service = document_service.vector_db
        collection = chroma_service.collection
        
        # 1. Проверяем общее количество документов
        total_count = collection.count()
        
        # 2. Получаем ВСЕ документы из коллекции
        all_docs = collection.get(
            include=["documents", "metadatas", "embeddings"]
        )
        
        # 3. Прямой поиск в ChromaDB без фильтров
        raw_search = collection.query(
            query_texts=[query],
            n_results=10,
            include=["documents", "metadatas", "distances"]
        )
        
        # 4. Поиск с очень низким порогом
        try:
            low_threshold_results = await document_service.search(
                query=query,
                limit=10,
                min_relevance=0.01  # 1%
            )
        except Exception as e:
            low_threshold_results = f"Error: {e}"
        
        # 5. Ищем наш документ в результатах
        target_doc_id = "tmpj4r82ypb.txt_c758312a"
        target_found = False
        target_info = None
        
        if all_docs["ids"] and target_doc_id in all_docs["ids"]:
            idx = all_docs["ids"].index(target_doc_id)
            target_info = {
                "id": target_doc_id,
                "content_preview": all_docs["documents"][idx][:200] + "...",
                "metadata": all_docs["metadatas"][idx],
                "has_embedding": all_docs["embeddings"] is not None and len(all_docs["embeddings"]) > idx
            }
            target_found = True
        
        # 6. Анализируем результаты поиска
        search_analysis = {
            "total_results": len(raw_search["documents"][0]) if raw_search["documents"] and raw_search["documents"][0] else 0,
            "results_details": []
        }
        
        if raw_search["documents"] and raw_search["documents"][0]:
            for i in range(len(raw_search["documents"][0])):
                result_detail = {
                    "id": raw_search["ids"][0][i],
                    "distance": raw_search["distances"][0][i],
                    "relevance_score": 1 - raw_search["distances"][0][i],
                    "content_preview": raw_search["documents"][0][i][:100] + "...",
                    "metadata": raw_search["metadatas"][0][i],
                    "is_target_doc": raw_search["ids"][0][i] == target_doc_id
                }
                search_analysis["results_details"].append(result_detail)
        
        # 7. Проверяем embedding функцию
        try:
            test_embedding = chroma_service.embedding_function([query])
            embedding_works = True
            embedding_dimension = len(test_embedding[0]) if test_embedding else 0
        except Exception as e:
            embedding_works = False
            embedding_dimension = 0
            test_embedding = f"Error: {e}"
        
        # 8. Текстовый поиск (простой)
        simple_text_matches = []
        if all_docs["documents"]:
            for i, doc_content in enumerate(all_docs["documents"]):
                if query.lower() in doc_content.lower():
                    simple_text_matches.append({
                        "id": all_docs["ids"][i],
                        "filename": all_docs["metadatas"][i].get("filename", "Unknown"),
                        "match_position": doc_content.lower().find(query.lower()),
                        "content_preview": doc_content[max(0, doc_content.lower().find(query.lower())-50):doc_content.lower().find(query.lower())+150]
                    })
        
        return {
            "debug_info": {
                "query": query,
                "chromadb_status": {
                    "total_documents_in_collection": total_count,
                    "collection_name": collection.name,
                    "embedding_function": str(chroma_service.embedding_function),
                    "embedding_works": embedding_works,
                    "embedding_dimension": embedding_dimension
                },
                "target_document": {
                    "found_in_collection": target_found,
                    "document_info": target_info
                },
                "raw_chromadb_search": search_analysis,
                "simple_text_search": {
                    "matches_found": len(simple_text_matches),
                    "matches": simple_text_matches
                },
                "service_search_results": {
                    "low_threshold_results": low_threshold_results if isinstance(low_threshold_results, str) else f"Found {len(low_threshold_results)} results"
                }
            },
            "recommendations": []
        }
        
    except Exception as e:
        logger.error(f"Debug ChromaDB error: {e}")
        return {
            "debug_info": {"error": str(e)},
            "recommendations": ["Check ChromaDB service status", "Verify embedding function"]
        }        

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