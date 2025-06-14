# ====================================
# ФАЙЛ: backend/utils/logger.py (УПРОЩЕННАЯ ВЕРСИЯ)
# Создать простой файл для избежания ImportError
# ====================================

"""
Простая конфигурация логирования для Legal Assistant
"""

import logging
import sys
import os
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Простая настройка логирования"""
    
    # Создаем папку для логов если нужно
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Настройка формата
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Базовая конфигурация
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Добавляем файловый handler если указан файл
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file {log_file}: {e}")
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=log_format,
        handlers=handlers,
        force=True  # Перезаписывает существующую конфигурацию
    )
    
    # Настройка уровней для внешних библиотек
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("📝 Logging configured successfully")
    
    return logger


class RequestLogger:
    """Простой логгер запросов"""
    
    def __init__(self, name: str = "request"):
        self.logger = logging.getLogger(name)
    
    def log_request(self, method: str, path: str, status: int = None):
        """Логирует запрос"""
        if status:
            self.logger.info(f"{method} {path} - {status}")
        else:
            self.logger.info(f"{method} {path}")


# Дефолтная настройка при импорте модуля
if not logging.getLogger().handlers:
    setup_logging()