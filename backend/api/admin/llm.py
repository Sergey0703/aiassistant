# ====================================
# ФАЙЛ: backend/api/admin/llm.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для админских endpoints управления LLM
# ====================================

"""
Admin LLM Endpoints - Админские endpoints для управления и мониторинга LLM
"""

from fastapi import APIRouter, HTTPException, Depends
import logging
import time
from typing import Optional, List, Dict, Any

from models.responses import SuccessResponse
from app.dependencies import get_llm_service, get_services_status
from app.config import settings, get_llm_config, validate_llm_config

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/llm/status")
async def get_llm_status(llm_service = Depends(get_llm_service)):
    """Получить подробный статус LLM сервиса"""
    try:
        # Получаем статус от сервиса
        service_status = await llm_service.get_service_status()
        
        # Добавляем конфигурацию
        config = get_llm_config()
        config_validation = validate_llm_config()
        
        # Добавляем системную информацию
        system_info = {
            "service_type": getattr(llm_service, 'service_type', 'real'),
            "fallback_mode": service_status.get("service_type") == "fallback",
            "config_valid": config_validation["valid"],
            "timestamp": time.time()
        }
        
        return {
            "service_status": service_status,
            "configuration": config,
            "config_validation": config_validation,
            "system_info": system_info
        }
        
    except Exception as e:
        logger.error(f"Error getting LLM status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM status: {str(e)}")

@router.get("/llm/models")
async def get_available_models(llm_service = Depends(get_llm_service)):
    """Получить список доступных моделей"""
    try:
        # Проверяем статус Ollama
        if hasattr(llm_service, 'ollama'):
            health = await llm_service.ollama.check_service_health()
            
            if health["available"]:
                return {
                    "available": True,
                    "models": health["models"],
                    "default_model": health["default_model"],
                    "base_url": health["base_url"],
                    "fallback_models": settings.OLLAMA_FALLBACK_MODELS,
                    "recommended_models": {
                        "fast": "llama3.2:1b",
                        "balanced": "llama3.2",
                        "quality": "llama3.1:8b",
                        "current": health["default_model"]
                    }
                }
            else:
                return {
                    "available": False,
                    "error": health.get("error"),
                    "base_url": health["base_url"],
                    "fallback_models": settings.OLLAMA_FALLBACK_MODELS,
                    "instructions": [
                        "Install Ollama from https://ollama.ai",
                        "Run: ollama pull llama3.2",
                        "Ensure Ollama is running on " + settings.OLLAMA_BASE_URL
                    ]
                }
        else:
            # Fallback service
            return {
                "available": False,
                "error": "LLM service in fallback mode",
                "recommendations": [
                    "Check Ollama installation",
                    "Verify OLLAMA_ENABLED=true in configuration",
                    "Restart the server after fixing issues"
                ]
            }
            
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@router.post("/llm/models/pull")
async def pull_model(
    model_name: str,
    llm_service = Depends(get_llm_service)
):
    """Загрузить новую модель в Ollama"""
    try:
        if not hasattr(llm_service, 'ollama'):
            raise HTTPException(status_code=503, detail="Ollama service not available")
        
        logger.info(f"🔄 Pulling model: {model_name}")
        
        # Запускаем загрузку модели
        result = await llm_service.ollama.pull_model(model_name)
        
        if result["success"]:
            logger.info(f"✅ Successfully pulled model: {model_name}")
            return SuccessResponse(
                message=f"Model '{model_name}' pulled successfully",
                data={
                    "model": model_name,
                    "pull_time": time.time(),
                    "available_models": await _get_model_list(llm_service)
                }
            )
        else:
            logger.error(f"❌ Failed to pull model {model_name}: {result['error']}")
            raise HTTPException(status_code=400, detail=f"Failed to pull model: {result['error']}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {str(e)}")

@router.post("/llm/test")
async def test_llm_generation(
    prompt: str = "What is law?",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    llm_service = Depends(get_llm_service)
):
    """Тестовый вызов LLM для проверки работоспособности"""
    try:
        logger.info(f"🧪 Testing LLM generation with prompt: '{prompt[:50]}...'")
        
        # Используем настройки по умолчанию если не указаны
        test_model = model or settings.OLLAMA_DEFAULT_MODEL
        test_temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        test_max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        # Тестируем через общий метод
        if hasattr(llm_service, 'ollama'):
            response = await llm_service.ollama.generate_response(
                prompt=prompt,
                model=test_model,
                temperature=test_temperature,
                max_tokens=test_max_tokens
            )
            
            return {
                "test_successful": response.success,
                "request": {
                    "prompt": prompt,
                    "model": test_model,
                    "temperature": test_temperature,
                    "max_tokens": test_max_tokens
                },
                "response": {
                    "content": response.content,
                    "model": response.model,
                    "tokens_used": response.tokens_used,
                    "response_time": response.response_time,
                    "success": response.success,
                    "error": response.error
                },
                "recommendations": _get_test_recommendations(response)
            }
        else:
            return {
                "test_successful": False,
                "error": "LLM service not available",
                "recommendations": [
                    "Check Ollama installation and configuration",
                    "Ensure Ollama is running on " + settings.OLLAMA_BASE_URL,
                    "Verify model is available: ollama list"
                ]
            }
            
    except Exception as e:
        logger.error(f"LLM test error: {e}")
        return {
            "test_successful": False,
            "error": str(e),
            "recommendations": [
                "Check Ollama service health",
                "Verify model exists",
                "Check server logs for details"
            ]
        }

@router.get("/llm/usage-stats")
async def get_llm_usage_stats():
    """Получить статистику использования LLM"""
    try:
        # Импортируем историю чатов для анализа
        from api.user.chat import chat_history
        
        # Анализируем использование AI
        total_messages = len(chat_history)
        ai_responses = 0
        total_tokens = 0
        total_time = 0.0
        models_used = {}
        errors = 0
        
        for entry in chat_history:
            ai_stats = entry.get("ai_stats", {})
            
            if ai_stats.get("ai_used", False):
                ai_responses += 1
                total_tokens += ai_stats.get("tokens_used", 0)
                total_time += ai_stats.get("response_time", 0)
                
                model = ai_stats.get("model", "unknown")
                models_used[model] = models_used.get(model, 0) + 1
            
            if ai_stats.get("error"):
                errors += 1
        
        # Вычисляем статистику
        ai_usage_rate = (ai_responses / total_messages * 100) if total_messages > 0 else 0
        avg_tokens = total_tokens / ai_responses if ai_responses > 0 else 0
        avg_time = total_time / ai_responses if ai_responses > 0 else 0
        error_rate = (errors / total_messages * 100) if total_messages > 0 else 0
        
        return {
            "usage_summary": {
                "total_messages": total_messages,
                "ai_responses": ai_responses,
                "ai_usage_rate": ai_usage_rate,
                "error_rate": error_rate
            },
            "performance": {
                "total_tokens_used": total_tokens,
                "average_tokens_per_response": avg_tokens,
                "total_generation_time": total_time,
                "average_response_time": avg_time
            },
            "models_usage": models_used,
            "recommendations": _get_usage_recommendations(ai_usage_rate, error_rate, avg_time)
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage stats: {str(e)}")

@router.post("/llm/clear-cache")
async def clear_llm_cache():
    """Очистить кэш LLM (если реализован)"""
    try:
        # Пока что простая заглушка
        # В будущем здесь может быть логика очистки кэша ответов
        
        logger.info("🧹 LLM cache cleared")
        
        return SuccessResponse(
            message="LLM cache cleared successfully",
            data={
                "cleared_at": time.time(),
                "note": "Cache clearing functionality to be implemented"
            }
        )
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/llm/config")
async def get_llm_configuration():
    """Получить текущую конфигурацию LLM"""
    try:
        config = get_llm_config()
        validation = validate_llm_config()
        
        # Добавляем текущие настройки сессии
        runtime_info = {
            "current_time": time.time(),
            "settings_source": "config.py",
            "environment_overrides": _get_env_overrides()
        }
        
        return {
            "configuration": config,
            "validation": validation,
            "runtime_info": runtime_info,
            "editable_settings": {
                "temperature": "LLM response creativity (0.0-1.0)",
                "max_tokens": "Maximum response length",
                "timeout": "Request timeout in seconds",
                "cache_enabled": "Enable response caching",
                "demo_mode": "Use demo responses instead of real AI"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")

@router.post("/llm/health-check")
async def run_llm_health_check(llm_service = Depends(get_llm_service)):
    """Запустить полную проверку здоровья LLM системы"""
    try:
        logger.info("🏥 Running comprehensive LLM health check...")
        
        health_results = {
            "timestamp": time.time(),
            "overall_status": "unknown",
            "checks": {}
        }
        
        # 1. Проверка доступности Ollama
        if hasattr(llm_service, 'ollama'):
            ollama_health = await llm_service.ollama.check_service_health()
            health_results["checks"]["ollama_service"] = {
                "status": "pass" if ollama_health["available"] else "fail",
                "details": ollama_health
            }
        else:
            health_results["checks"]["ollama_service"] = {
                "status": "fail",
                "details": {"error": "Ollama service not initialized"}
            }
        
        # 2. Проверка модели по умолчанию
        try:
            test_response = await llm_service.ollama.generate_response(
                prompt="Test prompt for health check",
                model=settings.OLLAMA_DEFAULT_MODEL,
                max_tokens=50
            )
            
            health_results["checks"]["default_model"] = {
                "status": "pass" if test_response.success else "fail",
                "details": {
                    "model": settings.OLLAMA_DEFAULT_MODEL,
                    "response_time": test_response.response_time,
                    "error": test_response.error
                }
            }
        except Exception as e:
            health_results["checks"]["default_model"] = {
                "status": "fail",
                "details": {"error": str(e)}
            }
        
        # 3. Проверка конфигурации
        config_validation = validate_llm_config()
        health_results["checks"]["configuration"] = {
            "status": "pass" if config_validation["valid"] else "warn",
            "details": config_validation
        }
        
        # Определяем общий статус
        statuses = [check["status"] for check in health_results["checks"].values()]
        if all(status == "pass" for status in statuses):
            health_results["overall_status"] = "healthy"
        elif any(status == "fail" for status in statuses):
            health_results["overall_status"] = "unhealthy"
        else:
            health_results["overall_status"] = "degraded"
        
        # Добавляем рекомендации
        health_results["recommendations"] = _get_health_recommendations(health_results["checks"])
        
        logger.info(f"🏥 Health check completed: {health_results['overall_status']}")
        
        return health_results
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# ====================================
# UTILITY FUNCTIONS
# ====================================

async def _get_model_list(llm_service) -> List[str]:
    """Получает список доступных моделей"""
    try:
        if hasattr(llm_service, 'ollama'):
            health = await llm_service.ollama.check_service_health()
            return health.get("models", [])
        return []
    except:
        return []

def _get_test_recommendations(response) -> List[str]:
    """Генерирует рекомендации на основе результата тестирования"""
    recommendations = []
    
    if not response.success:
        recommendations.append("Check Ollama service status")
        recommendations.append("Verify model is available")
        
        if "connection" in str(response.error).lower():
            recommendations.append("Ensure Ollama is running on " + settings.OLLAMA_BASE_URL)
        
        if "model" in str(response.error).lower():
            recommendations.append("Pull the required model: ollama pull " + settings.OLLAMA_DEFAULT_MODEL)
    
    elif response.response_time > 10:
        recommendations.append("Response time is slow - consider using a smaller model")
        recommendations.append("Check system resources (CPU/RAM usage)")
    
    elif response.tokens_used < 10:
        recommendations.append("Response seems very short - consider adjusting max_tokens")
    
    else:
        recommendations.append("LLM is working correctly")
    
    return recommendations

def _get_usage_recommendations(ai_usage_rate: float, error_rate: float, avg_time: float) -> List[str]:
    """Генерирует рекомендации по использованию"""
    recommendations = []
    
    if ai_usage_rate < 50:
        recommendations.append("AI usage rate is low - check if Ollama is consistently available")
    
    if error_rate > 20:
        recommendations.append("High error rate detected - check Ollama stability")
        recommendations.append("Consider increasing timeout settings")
    
    if avg_time > 5:
        recommendations.append("Average response time is high - consider using a faster model")
        recommendations.append("Check system performance and available resources")
    
    if not recommendations:
        recommendations.append("LLM performance is optimal")
    
    return recommendations

def _get_env_overrides() -> Dict[str, str]:
    """Получает переопределения из переменных окружения"""
    import os
    
    env_vars = [
        "OLLAMA_ENABLED", "OLLAMA_BASE_URL", "OLLAMA_DEFAULT_MODEL",
        "LLM_TEMPERATURE", "LLM_MAX_TOKENS", "LLM_DEMO_MODE"
    ]
    
    overrides = {}
    for var in env_vars:
        value = os.getenv(var)
        if value:
            overrides[var] = value
    
    return overrides

def _get_health_recommendations(checks: Dict) -> List[str]:
    """Генерирует рекомендации на основе проверок здоровья"""
    recommendations = []
    
    ollama_check = checks.get("ollama_service", {})
    if ollama_check.get("status") == "fail":
        recommendations.append("Install and start Ollama service")
        recommendations.append("Visit https://ollama.ai for installation instructions")
    
    model_check = checks.get("default_model", {})
    if model_check.get("status") == "fail":
        recommendations.append(f"Pull the default model: ollama pull {settings.OLLAMA_DEFAULT_MODEL}")
        recommendations.append("Ensure sufficient disk space for model storage")
    
    config_check = checks.get("configuration", {})
    if config_check.get("status") == "warn":
        recommendations.append("Review and fix configuration warnings")
    
    if not recommendations:
        recommendations.append("All LLM components are healthy")
    
    return recommendations