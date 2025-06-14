# ====================================
# ФАЙЛ: backend/utils/helpers.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для вспомогательных функций
# ====================================

"""
Вспомогательные функции для приложения
"""

import re
import time
import hashlib
import json
import os
import tempfile
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, unquote
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ====================================
# РАБОТА С ФАЙЛАМИ
# ====================================

def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """Проверяет, разрешен ли тип файла"""
    if not filename:
        return False
    
    file_extension = Path(filename).suffix.lower()
    return file_extension in [ext.lower() for ext in allowed_extensions]

def get_file_mime_type(filename: str) -> str:
    """Определяет MIME тип файла"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

def format_file_size(size_bytes: int) -> str:
    """Форматирует размер файла в человекочитаемый вид"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """Очищает имя файла от недопустимых символов"""
    # Удаляем недопустимые символы
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Удаляем лишние пробелы и точки
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.strip('.')
    
    # Ограничиваем длину
    if len(cleaned) > 200:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:200-len(ext)] + ext
    
    return cleaned or "unnamed_file"

def generate_unique_filename(base_name: str, directory: str) -> str:
    """Генерирует уникальное имя файла в директории"""
    base_path = Path(directory)
    name = Path(base_name).stem
    extension = Path(base_name).suffix
    
    counter = 1
    new_name = base_name
    
    while (base_path / new_name).exists():
        new_name = f"{name}_{counter}{extension}"
        counter += 1
    
    return new_name

# ====================================
# РАБОТА С ТЕКСТОМ
# ====================================

def clean_text(text: str) -> str:
    """Очищает текст от лишних символов и форматирует"""
    if not text:
        return ""
    
    # Убираем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Убираем повторяющиеся символы
    text = re.sub(r'\.{3,}', '...', text)
    text = re.sub(r'-{3,}', '---', text)
    text = re.sub(r'={3,}', '===', text)
    
    # Убираем управляющие символы
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()

def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
    """Извлекает ключевые слова из текста"""
    if not text:
        return []
    
    # Простое извлечение слов
    words = re.findall(r'\b[a-zA-Zа-яА-Я]{' + str(min_length) + ',}\b', text.lower())
    
    # Подсчитываем частоту
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Сортируем по частоте и возвращаем топ
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]

def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Обрезает текст до указанной длины"""
    if len(text) <= max_length:
        return text
    
    # Пытаемся обрезать по предложениям
    truncated = text[:max_length - len(suffix)]
    last_sentence = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if last_sentence > max_length * 0.7:  # Если нашли предложение в разумном месте
        return truncated[:last_sentence + 1] + suffix
    else:
        return truncated + suffix

def detect_language(text: str) -> str:
    """Простое определение языка текста"""
    if not text:
        return "unknown"
    
    # Подсчитываем символы разных алфавитов
    cyrillic_count = len(re.findall(r'[а-яё]', text.lower()))
    latin_count = len(re.findall(r'[a-z]', text.lower()))
    
    total_letters = cyrillic_count + latin_count
    
    if total_letters == 0:
        return "unknown"
    
    cyrillic_ratio = cyrillic_count / total_letters
    
    if cyrillic_ratio > 0.6:
        return "uk"  # или "ru"
    elif cyrillic_ratio < 0.2:
        return "en"
    else:
        return "mixed"

# ====================================
# РАБОТА С URL
# ====================================

def validate_url(url: str) -> Dict[str, Any]:
    """Валидирует URL и возвращает информацию о нем"""
    result = {
        "valid": False,
        "url": url,
        "scheme": "",
        "domain": "",
        "path": "",
        "errors": [],
        "warnings": []
    }
    
    try:
        parsed = urlparse(url)
        
        result["scheme"] = parsed.scheme
        result["domain"] = parsed.netloc
        result["path"] = parsed.path
        
        # Проверки
        if not parsed.scheme:
            result["errors"].append("Missing URL scheme (http/https)")
        elif parsed.scheme not in ["http", "https"]:
            result["errors"].append(f"Unsupported scheme: {parsed.scheme}")
        
        if not parsed.netloc:
            result["errors"].append("Missing domain name")
        
        # Предупреждения
        if parsed.netloc in ["localhost", "127.0.0.1", "0.0.0.0"]:
            result["warnings"].append("Local URLs may not be accessible")
        
        if parsed.netloc.endswith(".local"):
            result["warnings"].append("Local domain detected")
        
        result["valid"] = len(result["errors"]) == 0
        
    except Exception as e:
        result["errors"].append(f"URL parsing error: {str(e)}")
    
    return result

def extract_domain(url: str) -> str:
    """Извлекает домен из URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""

def is_same_domain(url1: str, url2: str) -> bool:
    """Проверяет, принадлежат ли URL одному домену"""
    return extract_domain(url1) == extract_domain(url2)

# ====================================
# РАБОТА С ДАННЫМИ
# ====================================

def generate_hash(data: Union[str, bytes], algorithm: str = "md5") -> str:
    """Генерирует хэш для данных"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    if algorithm == "md5":
        return hashlib.md5(data).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

def generate_id(prefix: str = "", length: int = 8) -> str:
    """Генерирует уникальный ID"""
    timestamp = str(int(time.time()))
    random_part = generate_hash(timestamp + str(time.time()))[:length]
    
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part

def safe_json_load(file_path: str, default: Any = None) -> Any:
    """Безопасно загружает JSON файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load JSON from {file_path}: {e}")
        return default

def safe_json_save(data: Any, file_path: str) -> bool:
    """Безопасно сохраняет данные в JSON файл"""
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Сохраняем во временный файл сначала
        temp_path = file_path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Переименовываем после успешной записи
        os.rename(temp_path, file_path)
        return True
        
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return False

# ====================================
# РАБОТА СО ВРЕМЕНЕМ
# ====================================

def format_timestamp(timestamp: float, format_type: str = "datetime") -> str:
    """Форматирует timestamp в читаемый вид"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        
        if format_type == "datetime":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time":
            return dt.strftime("%H:%M:%S")
        elif format_type == "relative":
            return format_relative_time(timestamp)
        else:
            return dt.isoformat()
    except:
        return "Invalid timestamp"

def format_relative_time(timestamp: float) -> str:
    """Форматирует время относительно текущего момента"""
    try:
        now = time.time()
        diff = now - timestamp
        
        if diff < 60:
            return "Just now"
        elif diff < 3600:
            minutes = int(diff / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < 86400:
            hours = int(diff / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < 2592000:  # 30 days
            days = int(diff / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return format_timestamp(timestamp, "date")
    except:
        return "Unknown time"

def parse_time_period(period_str: str) -> timedelta:
    """Парсит строку времени в timedelta"""
    pattern = r'(\d+)([hdwmy])'
    matches = re.findall(pattern, period_str.lower())
    
    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit == 'h':
            total_seconds += value * 3600
        elif unit == 'd':
            total_seconds += value * 86400
        elif unit == 'w':
            total_seconds += value * 604800
        elif unit == 'm':
            total_seconds += value * 2592000  # 30 days
        elif unit == 'y':
            total_seconds += value * 31536000  # 365 days
    
    return timedelta(seconds=total_seconds)

# ====================================
# ВАЛИДАЦИЯ И ОЧИСТКА
# ====================================

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Очищает пользовательский ввод"""
    if not isinstance(text, str):
        return ""
    
    # Удаляем потенциально опасные символы
    text = re.sub(r'[<>"\']', '', text)
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length]
    
    # Очищаем пробелы
    text = text.strip()
    
    return text

def validate_category(category: str, allowed_categories: List[str]) -> bool:
    """Проверяет валидность категории"""
    return category in allowed_categories

def validate_pagination(offset: int, limit: int, max_limit: int = 100) -> Dict[str, int]:
    """Валидирует параметры пагинации"""
    offset = max(0, offset)
    limit = max(1, min(limit, max_limit))
    
    return {"offset": offset, "limit": limit}

# ====================================
# СИСТЕМА УВЕДОМЛЕНИЙ
# ====================================

class NotificationManager:
    """Менеджер уведомлений для админ панели"""
    
    def __init__(self):
        self.notifications = []
    
    def add_notification(self, message: str, type_: str = "info", duration: int = 5000):
        """Добавляет уведомление"""
        notification = {
            "id": generate_id("notif"),
            "message": message,
            "type": type_,
            "duration": duration,
            "created_at": time.time()
        }
        self.notifications.append(notification)
        
        # Ограничиваем количество уведомлений
        if len(self.notifications) > 50:
            self.notifications = self.notifications[-50:]
    
    def get_notifications(self, since: float = None) -> List[Dict]:
        """Получает уведомления"""
        if since:
            return [n for n in self.notifications if n["created_at"] > since]
        return self.notifications.copy()
    
    def clear_notifications(self):
        """Очищает уведомления"""
        self.notifications.clear()

# Глобальный экземпляр менеджера уведомлений
notification_manager = NotificationManager()

# ====================================
# МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ
# ====================================

class PerformanceTimer:
    """Контекстный менеджер для измерения производительности"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"⏱️ {self.operation_name} completed in {duration:.3f}s")
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

# ====================================
# КОНФИГУРАЦИЯ И НАСТРОЙКИ
# ====================================

def load_config_with_defaults(config_path: str, defaults: Dict) -> Dict:
    """Загружает конфигурацию с дефолтными значениями"""
    config = defaults.copy()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
    
    return config

def ensure_directory_exists(directory: str) -> bool:
    """Создает директорию если она не существует"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False

# ====================================
# ЭКСПОРТ ФУНКЦИЙ
# ====================================

__all__ = [
    # Файлы
    'validate_file_type', 'get_file_mime_type', 'format_file_size',
    'clean_filename', 'generate_unique_filename',
    
    # Текст
    'clean_text', 'extract_keywords', 'truncate_text', 'detect_language',
    
    # URL
    'validate_url', 'extract_domain', 'is_same_domain',
    
    # Данные
    'generate_hash', 'generate_id', 'safe_json_load', 'safe_json_save',
    
    # Время
    'format_timestamp', 'format_relative_time', 'parse_time_period',
    
    # Валидация
    'sanitize_input', 'validate_category', 'validate_pagination',
    
    # Классы
    'NotificationManager', 'PerformanceTimer', 'notification_manager',
    
    # Утилиты
    'load_config_with_defaults', 'ensure_directory_exists'
]