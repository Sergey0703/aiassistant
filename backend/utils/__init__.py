# ====================================
# ФАЙЛ: backend/utils/__init__.py (УПРОЩЕННАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
Utils Package - Пакет вспомогательных функций и утилит
"""

import logging

# Создаем правильный logger для этого модуля
_logger = logging.getLogger(__name__)

# Версия пакета utils
__version__ = "2.0.0"

# Метаданные пакета
__author__ = "Legal Assistant Team"
__description__ = "Utility functions and helpers for Legal Assistant API"

# Пытаемся импортировать функции из helpers
try:
    from .helpers import (
        # Работа с файлами
        validate_file_type,
        get_file_mime_type,
        format_file_size,
        clean_filename,
        generate_unique_filename,
        
        # Обработка текста
        clean_text,
        extract_keywords,
        truncate_text,
        detect_language,
        
        # Работа с URL
        validate_url,
        extract_domain,
        is_same_domain,
        
        # Управление данными
        generate_hash,
        generate_id,
        safe_json_load,
        safe_json_save,
        
        # Работа со временем
        format_timestamp,
        format_relative_time,
        parse_time_period,
        
        # Валидация и очистка
        sanitize_input,
        validate_category,
        validate_pagination,
        
        # Классы
        NotificationManager,
        PerformanceTimer,
        notification_manager,
        
        # Конфигурация
        load_config_with_defaults,
        ensure_directory_exists
    )
    _helpers_available = True
    print("✅ Helpers imported successfully")
    
except ImportError as e:
    _helpers_available = False
    print(f"⚠️ Helpers import failed: {e}")
    
    # Создаем заглушки для критических функций
    def validate_file_type(*args, **kwargs):
        return False
    
    def clean_text(text):
        return text.strip() if text else ""
    
    def generate_id(*args, **kwargs):
        import time
        return str(int(time.time()))
    
    def safe_json_load(file_path, default=None):
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    
    def safe_json_save(data, file_path):
        try:
            import json
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

# Пытаемся импортировать логгер
try:
    from .logger import setup_logging, RequestLogger
    _logger_available = True
    print("✅ Logger imported successfully")
    
except ImportError as e:
    _logger_available = False
    print(f"⚠️ Logger import failed: {e}")
    
    # Заглушка для setup_logging
    def setup_logging(log_level="INFO", log_file=None):
        import logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        return logging.getLogger(__name__)
    
    # Заглушка для RequestLogger
    class RequestLogger:
        def __init__(self, *args, **kwargs):
            self.logger = logging.getLogger("request")
        
        def log_request(self, method, path, status=None):
            if status:
                self.logger.info(f"{method} {path} - {status}")
            else:
                self.logger.info(f"{method} {path}")

# Базовая конфигурация
DEFAULT_CONFIG = {
    "file_size_limit": 10 * 1024 * 1024,  # 10MB
    "text_length_limit": 10000,           # 10K символов
    "cache_ttl": 300,                     # 5 минут
    "rate_limit": 100,                    # 100 запросов в час
    "log_level": "INFO"
}

class UtilsConfig:
    """Простая конфигурация для utils пакета"""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
    
    def update(self, **kwargs):
        self.config.update(kwargs)

# Глобальный экземпляр конфигурации
config = UtilsConfig()

# Функции быстрого доступа
def get_config(key, default=None):
    return config.get(key, default)

def set_config(key, value):
    config.set(key, value)

def initialize_utils(custom_config=None):
    """Инициализирует utils пакет"""
    if custom_config:
        config.update(**custom_config)
    
    # Создаем необходимые директории
    directories = ["logs", "cache", "temp", "backups"]
    for directory in directories:
        try:
            import os
            os.makedirs(directory, exist_ok=True)
        except:
            pass
    
    print("✅ Utils package initialized")

def get_utils_info():
    """Возвращает информацию о пакете utils"""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "helpers_available": _helpers_available,
        "logger_available": _logger_available,
        "config": config.config
    }

# Экспорт основных компонентов
__all__ = [
    # Метаданные
    '__version__',
    '__author__',
    '__description__',
    
    # Конфигурация
    'config',
    'get_config',
    'set_config',
    'initialize_utils',
    'get_utils_info',
    'DEFAULT_CONFIG',
    'UtilsConfig',
    
    # Логирование
    'setup_logging',
    'RequestLogger',
    
    # Основные функции (всегда доступны через заглушки)
    'clean_text',
    'generate_id',
    'safe_json_load',
    'safe_json_save',
    'validate_file_type'
]

# Добавляем функции из helpers если они доступны
if _helpers_available:
    __all__.extend([
        'get_file_mime_type', 'format_file_size', 'clean_filename',
        'generate_unique_filename', 'extract_keywords', 'truncate_text',
        'detect_language', 'validate_url', 'extract_domain', 'is_same_domain',
        'generate_hash', 'format_timestamp', 'format_relative_time',
        'parse_time_period', 'sanitize_input', 'validate_category',
        'validate_pagination', 'NotificationManager', 'PerformanceTimer',
        'notification_manager', 'load_config_with_defaults', 'ensure_directory_exists'
    ])

# Автоматическая инициализация
try:
    initialize_utils()
except Exception as e:
    print(f"⚠️ Auto-initialization failed: {e}")

print(f"📦 Utils package loaded ({len(__all__)} items available)")