# ====================================
# ФАЙЛ: backend/app/middleware.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для middleware FastAPI приложения
# ====================================

"""
Middleware для FastAPI приложения Legal Assistant
"""

import time
import logging
import json
import uuid
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from urllib.parse import urlparse

from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware as StarletteBaseMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from utils.helpers import notification_manager, PerformanceTimer
from app.config import settings

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов и ответов"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.sensitive_paths = {"/admin", "/api/admin"}
        self.excluded_paths = {"/docs", "/redoc", "/openapi.json", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Генерируем уникальный ID запроса
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Добавляем ID запроса в контекст
        request.state.request_id = request_id
        
        # Получаем информацию о клиенте
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Логируем входящий запрос
        path = request.url.path
        method = request.method
        
        if path not in self.excluded_paths:
            logger.info(
                f"🌐 [{request_id}] {method} {path} - "
                f"IP: {client_ip} - UA: {user_agent[:50]}..."
            )
        
        try:
            # Обрабатываем запрос
            response = await call_next(request)
            
            # Вычисляем время обработки
            process_time = time.time() - start_time
            
            # Добавляем заголовки
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 3))
            
            # Логируем ответ
            if path not in self.excluded_paths:
                status_emoji = "✅" if response.status_code < 400 else "❌"
                logger.info(
                    f"{status_emoji} [{request_id}] {method} {path} - "
                    f"Status: {response.status_code} - "
                    f"Time: {process_time:.3f}s"
                )
            
            # Отправляем уведомление для админ панели
            if path.startswith("/api/admin") and response.status_code >= 400:
                notification_manager.add_notification(
                    f"Admin API error: {method} {path} returned {response.status_code}",
                    "error"
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                f"❌ [{request_id}] {method} {path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Отправляем уведомление об ошибке
            notification_manager.add_notification(
                f"Server error on {method} {path}: {str(e)}",
                "error"
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Получает IP адрес клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback к прямому подключению
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware для безопасности"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.blocked_ips = set()
        self.rate_limit_storage = {}  # IP -> {count, reset_time}
        self.rate_limit_requests = 100  # Запросов
        self.rate_limit_window = 3600   # За час
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        
        # Проверяем заблокированные IP
        if client_ip in self.blocked_ips:
            logger.warning(f"🚫 Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # Проверяем rate limiting
        if self._is_rate_limited(client_ip):
            logger.warning(f"⚠️ Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        
        # Проверяем подозрительные паттерны
        if self._is_suspicious_request(request):
            logger.warning(f"🔍 Suspicious request from {client_ip}: {request.url.path}")
            # Можно заблокировать IP или просто логировать
            
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Добавляем security заголовки
        self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Получает IP адрес клиента (дублирует логику из RequestLoggingMiddleware)"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Проверяет rate limiting для IP"""
        now = time.time()
        
        if client_ip not in self.rate_limit_storage:
            self.rate_limit_storage[client_ip] = {
                "count": 1,
                "reset_time": now + self.rate_limit_window
            }
            return False
        
        ip_data = self.rate_limit_storage[client_ip]
        
        # Сбрасываем счетчик если окно истекло
        if now > ip_data["reset_time"]:
            ip_data["count"] = 1
            ip_data["reset_time"] = now + self.rate_limit_window
            return False
        
        # Увеличиваем счетчик
        ip_data["count"] += 1
        
        # Проверяем лимит
        return ip_data["count"] > self.rate_limit_requests
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Определяет подозрительные запросы"""
        path = request.url.path.lower()
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Подозрительные пути
        suspicious_paths = [
            "/.env", "/wp-admin", "/admin.php", "/phpmyadmin",
            "/wp-login.php", "/.git", "/config", "/backup"
        ]
        
        if any(suspicious in path for suspicious in suspicious_paths):
            return True
        
        # Подозрительные User-Agent
        suspicious_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap",
            "burpsuite", "w3af", "acunetix"
        ]
        
        if any(agent in user_agent for agent in suspicious_agents):
            return True
        
        # Слишком длинные пути
        if len(path) > 500:
            return True
        
        return False
    
    def _add_security_headers(self, response: Response):
        """Добавляет security заголовки"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware для обработки ошибок"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # HTTP исключения обрабатываются FastAPI автоматически
            raise
            
        except Exception as e:
            # Неожиданные ошибки
            request_id = getattr(request.state, "request_id", "unknown")
            
            logger.error(
                f"💥 [{request_id}] Unhandled exception: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            
            # Отправляем уведомление
            notification_manager.add_notification(
                f"Unhandled server error: {type(e).__name__}",
                "error"
            )
            
            # Возвращаем общую ошибку (не раскрываем детали)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            )

class DatabaseMiddleware(BaseHTTPMiddleware):
    """Middleware для мониторинга базы данных"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.db_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "average_query_time": 0.0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Засекаем время до запроса
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Вычисляем время обработки
            process_time = time.time() - start_time
            
            # Обновляем статистику (приблизительно)
            self._update_db_stats(process_time, success=True)
            
            # Добавляем заголовки с информацией о БД
            if hasattr(request.state, "db_queries"):
                response.headers["X-DB-Queries"] = str(request.state.db_queries)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            self._update_db_stats(process_time, success=False)
            raise
    
    def _update_db_stats(self, process_time: float, success: bool):
        """Обновляет статистику базы данных"""
        self.db_stats["total_queries"] += 1
        
        if not success:
            self.db_stats["failed_queries"] += 1
        
        if process_time > 1.0:  # Медленные запросы > 1 секунды
            self.db_stats["slow_queries"] += 1
        
        # Обновляем среднее время
        total = self.db_stats["total_queries"]
        current_avg = self.db_stats["average_query_time"]
        self.db_stats["average_query_time"] = (
            (current_avg * (total - 1) + process_time) / total
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику базы данных"""
        total = self.db_stats["total_queries"]
        return {
            **self.db_stats,
            "success_rate": ((total - self.db_stats["failed_queries"]) / total * 100) if total > 0 else 0,
            "slow_query_rate": (self.db_stats["slow_queries"] / total * 100) if total > 0 else 0
        }

class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware для кэширования ответов"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cache = {}  # Простой in-memory кэш
        self.cache_ttl = 300  # 5 минут
        self.cacheable_paths = {"/api/user/search/categories", "/api/admin/stats"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Проверяем можно ли кэшировать этот запрос
        if not self._is_cacheable(request):
            return await call_next(request)
        
        # Генерируем ключ кэша
        cache_key = self._generate_cache_key(request)
        
        # Проверяем кэш
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            logger.debug(f"📦 Cache hit for {request.url.path}")
            cached_response.headers["X-Cache-Status"] = "HIT"
            return cached_response
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Кэшируем успешные ответы
        if response.status_code == 200:
            self._store_in_cache(cache_key, response)
            response.headers["X-Cache-Status"] = "MISS"
        else:
            response.headers["X-Cache-Status"] = "SKIP"
        
        return response
    
    def _is_cacheable(self, request: Request) -> bool:
        """Определяет можно ли кэшировать запрос"""
        # Кэшируем только GET запросы
        if request.method != "GET":
            return False
        
        # Проверяем путь
        path = request.url.path
        return any(cacheable_path in path for cacheable_path in self.cacheable_paths)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Генерирует ключ кэша"""
        # Включаем путь и query параметры
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Добавляем заголовки которые влияют на ответ
        accept_language = request.headers.get("accept-language", "")
        if accept_language:
            key_parts.append(accept_language)
        
        return "|".join(key_parts)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Response]:
        """Получает ответ из кэша"""
        if cache_key not in self.cache:
            return None
        
        cached_item = self.cache[cache_key]
        
        # Проверяем TTL
        if time.time() > cached_item["expires_at"]:
            del self.cache[cache_key]
            return None
        
        return cached_item["response"]
    
    def _store_in_cache(self, cache_key: str, response: Response):
        """Сохраняет ответ в кэш"""
        try:
            # Клонируем ответ для кэша
            cached_response = Response(
                content=response.body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            self.cache[cache_key] = {
                "response": cached_response,
                "expires_at": time.time() + self.cache_ttl,
                "created_at": time.time()
            }
            
            # Ограничиваем размер кэша
            if len(self.cache) > 100:
                # Удаляем самые старые записи
                sorted_items = sorted(
                    self.cache.items(),
                    key=lambda x: x[1]["created_at"]
                )
                for old_key, _ in sorted_items[:20]:
                    del self.cache[old_key]
                    
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    def clear_cache(self):
        """Очищает кэш"""
        self.cache.clear()
        logger.info("🧹 Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        return {
            "cached_items": len(self.cache),
            "cache_size_mb": sum(
                len(str(item["response"].body)) 
                for item in self.cache.values()
            ) / 1024 / 1024,
            "oldest_item": min(
                (item["created_at"] for item in self.cache.values()),
                default=0
            ),
            "newest_item": max(
                (item["created_at"] for item in self.cache.values()),
                default=0
            )
        }

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора метрик"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "requests_by_method": {},
            "requests_by_path": {},
            "response_times": [],
            "status_codes": {},
            "user_agents": {},
            "errors": []
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Увеличиваем счетчики
        self.metrics["total_requests"] += 1
        
        method = request.method
        self.metrics["requests_by_method"][method] = (
            self.metrics["requests_by_method"].get(method, 0) + 1
        )
        
        path = request.url.path
        self.metrics["requests_by_path"][path] = (
            self.metrics["requests_by_path"].get(path, 0) + 1
        )
        
        user_agent = request.headers.get("user-agent", "Unknown")[:50]
        self.metrics["user_agents"][user_agent] = (
            self.metrics["user_agents"].get(user_agent, 0) + 1
        )
        
        try:
            response = await call_next(request)
            
            # Записываем время ответа
            response_time = time.time() - start_time
            self.metrics["response_times"].append(response_time)
            
            # Ограничиваем размер списка времен ответа
            if len(self.metrics["response_times"]) > 1000:
                self.metrics["response_times"] = self.metrics["response_times"][-500:]
            
            # Записываем статус код
            status = response.status_code
            self.metrics["status_codes"][status] = (
                self.metrics["status_codes"].get(status, 0) + 1
            )
            
            return response
            
        except Exception as e:
            # Записываем ошибку
            error_info = {
                "timestamp": time.time(),
                "path": path,
                "method": method,
                "error": str(e),
                "type": type(e).__name__
            }
            self.metrics["errors"].append(error_info)
            
            # Ограничиваем размер списка ошибок
            if len(self.metrics["errors"]) > 100:
                self.metrics["errors"] = self.metrics["errors"][-50:]
            
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает метрики"""
        response_times = self.metrics["response_times"]
        
        metrics = self.metrics.copy()
        
        if response_times:
            metrics["average_response_time"] = sum(response_times) / len(response_times)
            metrics["min_response_time"] = min(response_times)
            metrics["max_response_time"] = max(response_times)
            
            # Перцентили
            sorted_times = sorted(response_times)
            metrics["p50_response_time"] = sorted_times[len(sorted_times) // 2]
            metrics["p95_response_time"] = sorted_times[int(len(sorted_times) * 0.95)]
            metrics["p99_response_time"] = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            metrics.update({
                "average_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "p50_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0
            })
        
        # Удаляем сырые данные из ответа
        metrics.pop("response_times", None)
        
        return metrics
    
    def reset_metrics(self):
        """Сбрасывает метрики"""
        self.metrics = {
            "total_requests": 0,
            "requests_by_method": {},
            "requests_by_path": {},
            "response_times": [],
            "status_codes": {},
            "user_agents": {},
            "errors": []
        }

# Глобальные экземпляры middleware для доступа к статистике
database_middleware = DatabaseMiddleware
cache_middleware = CacheMiddleware
metrics_middleware = MetricsMiddleware

# Функция для настройки всех middleware
def setup_middleware(app):
    """Настраивает все middleware для приложения"""
    
    # Порядок важен! Middleware применяются в обратном порядке
    
    # 1. Метрики (самый внешний слой)
    app.add_middleware(MetricsMiddleware)
    
    # 2. Кэширование
    app.add_middleware(CacheMiddleware)
    
    # 3. Мониторинг БД
    app.add_middleware(DatabaseMiddleware)
    
    # 4. Обработка ошибок
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 5. Безопасность
    app.add_middleware(SecurityMiddleware)
    
    # 6. Логирование (самый внутренний слой)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("✅ All middleware configured successfully")

# Экспорт
__all__ = [
    'RequestLoggingMiddleware',
    'SecurityMiddleware', 
    'ErrorHandlingMiddleware',
    'DatabaseMiddleware',
    'CacheMiddleware',
    'MetricsMiddleware',
    'setup_middleware'
]