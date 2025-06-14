# ====================================
# ФАЙЛ: backend/utils/logger.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для настройки логирования
# ====================================

"""
Конфигурация логирования для приложения
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Настройка логирования для всего приложения"""
    
    # Создаем папку для логов если нужно
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Настройка формата
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Базовая конфигурация
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Добавляем файловый handler если указан файл
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logging.getLogger().addHandler(file_handler)
    
    # Настройка уровней для внешних библиотек
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Снижаем уровень для ChromaDB если используется
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("📝 Logging configured successfully")
    
    return logger

class RequestLogger:
    """Middleware для логирования запросов"""
    
    def __init__(self, name: str = "request"):
        self.logger = logging.getLogger(name)
    
    async def __call__(self, request, call_next):
        start_time = datetime.now()
        
        # Логируем входящий запрос
        self.logger.info(f"🌐 {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # Вычисляем время обработки
            process_time = (datetime.now() - start_time).total_seconds()
            
            # Логируем ответ
            self.logger.info(
                f"✅ {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            process_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(
                f"❌ {request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            
            raise