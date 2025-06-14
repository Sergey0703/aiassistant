# ====================================
# ФАЙЛ: backend/app/config.py (ОБНОВЛЕННАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
Конфигурация приложения с настройками LLM
"""

# Пытаемся импортировать pydantic_settings с fallback
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback для старых версий pydantic
    try:
        from pydantic import BaseSettings
    except ImportError:
        # Если и BaseSettings недоступен, создаем заглушку
        print("⚠️ Pydantic not available, using basic configuration")
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            
            class Config:
                env_file = ".env"
                case_sensitive = True

from typing import List
import os

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API конфигурация
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Legal Assistant API"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "AI Legal Assistant with document scraping and vector search"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # База данных
    USE_CHROMADB: bool = True
    CHROMADB_PATH: str = "./chromadb_data"
    SIMPLE_DB_PATH: str = "./simple_db"
    
    # Файлы
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".txt", ".pdf", ".docx", ".md", ".doc"]
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    
    # Эмбеддинги
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Парсинг сайтов
    SCRAPING_DELAY: float = 1.5
    SCRAPING_TIMEOUT: int = 15
    MAX_URLS_PER_REQUEST: int = 20
    
    # Поиск
    DEFAULT_SEARCH_LIMIT: int = 5
    MAX_SEARCH_LIMIT: int = 50
    
    # ====================================
    # НОВЫЕ НАСТРОЙКИ LLM
    # ====================================
    
    # Ollama конфигурация
    OLLAMA_ENABLED: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3:latest"  # ИСПРАВЛЕНО для ваших моделей
    OLLAMA_FALLBACK_MODELS: List[str] = ["llama3:latest", "llama3:8b"]  # ИСПРАВЛЕНО
    
    # Параметры генерации
    LLM_TEMPERATURE: float = 0.3  # Низкая для юридических вопросов
    LLM_MAX_TOKENS: int = 1500
    LLM_TIMEOUT: int = 120  # секунд (увеличено с 60)
    
    # Управление контекстом
    MAX_CONTEXT_DOCUMENTS: int = 3  # Максимум документов в контексте
    MAX_CONTEXT_LENGTH: int = 4000  # Максимальная длина контекста
    CONTEXT_TRUNCATE_LENGTH: int = 1500  # Длина каждого документа в контексте
    
    # Режимы работы
    LLM_DEMO_MODE: bool = False  # Если True, показывает заглушки вместо реальных ответов
    LLM_FALLBACK_ENABLED: bool = True  # Включить fallback если LLM недоступен
    
    # Кэширование ответов
    LLM_CACHE_ENABLED: bool = True
    LLM_CACHE_TTL: int = 3600  # 1 час
    LLM_CACHE_MAX_SIZE: int = 100  # Максимум кэшированных ответов
    
    # Мониторинг и лимиты
    LLM_RATE_LIMIT: int = 60  # Запросов в час на пользователя
    LLM_DAILY_LIMIT: int = 500  # Запросов в день
    LLM_LOG_REQUESTS: bool = True  # Логировать все запросы к LLM
    
    # Языковые настройки
    SUPPORTED_LANGUAGES: List[str] = ["en", "uk"]
    DEFAULT_LANGUAGE: str = "en"
    
    # Промпт настройки
    SYSTEM_PROMPT_MAX_LENGTH: int = 1000
    USER_PROMPT_MAX_LENGTH: int = 2000
    
    def __init__(self, **kwargs):
        # Инициализация с возможностью работы без pydantic
        try:
            super().__init__(**kwargs)
        except Exception:
            # Если pydantic не работает, инициализируем вручную
            for key, value in kwargs.items():
                setattr(self, key, value)
            self._load_from_env()
    
    def _load_from_env(self):
        """Загружает настройки из переменных окружения"""
        env_mappings = {
            'USE_CHROMADB': ('USE_CHROMADB', lambda x: x.lower() in ['true', '1', 'yes']),
            'MAX_FILE_SIZE': ('MAX_FILE_SIZE', int),
            'LOG_LEVEL': ('LOG_LEVEL', str),
            'SCRAPING_DELAY': ('SCRAPING_DELAY', float),
            'DEFAULT_SEARCH_LIMIT': ('DEFAULT_SEARCH_LIMIT', int),
            
            # LLM настройки из переменных окружения
            'OLLAMA_ENABLED': ('OLLAMA_ENABLED', lambda x: x.lower() in ['true', '1', 'yes']),
            'OLLAMA_BASE_URL': ('OLLAMA_BASE_URL', str),
            'OLLAMA_DEFAULT_MODEL': ('OLLAMA_DEFAULT_MODEL', str),
            'LLM_TEMPERATURE': ('LLM_TEMPERATURE', float),
            'LLM_MAX_TOKENS': ('LLM_MAX_TOKENS', int),
            'LLM_DEMO_MODE': ('LLM_DEMO_MODE', lambda x: x.lower() in ['true', '1', 'yes']),
            'LLM_CACHE_ENABLED': ('LLM_CACHE_ENABLED', lambda x: x.lower() in ['true', '1', 'yes'])
        }
        
        for attr_name, (env_name, converter) in env_mappings.items():
            env_value = os.getenv(env_name)
            if env_value:
                try:
                    setattr(self, attr_name, converter(env_value))
                except (ValueError, TypeError):
                    pass  # Используем значение по умолчанию
    
    # Добавляем Config только если BaseSettings поддерживает его
    try:
        class Config:
            env_file = ".env"
            case_sensitive = True
    except:
        pass

# Создаем глобальный экземпляр настроек
try:
    settings = Settings()
    print("✅ Settings loaded successfully")
except Exception as e:
    print(f"⚠️ Could not create Settings with pydantic: {e}")
    print("Using fallback configuration...")
    
    # Fallback конфигурация
    class FallbackSettings:
        def __init__(self):
            self.API_V1_PREFIX = "/api"
            self.PROJECT_NAME = "Legal Assistant API"
            self.VERSION = "2.0.0"
            self.DESCRIPTION = "AI Legal Assistant with document scraping and vector search"
            self.CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
            self.USE_CHROMADB = True
            self.CHROMADB_PATH = "./chromadb_data"
            self.SIMPLE_DB_PATH = "./simple_db"
            self.MAX_FILE_SIZE = 10 * 1024 * 1024
            self.ALLOWED_FILE_TYPES = [".txt", ".pdf", ".docx", ".md", ".doc"]
            self.LOG_LEVEL = "INFO"
            self.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
            self.CHUNK_SIZE = 1000
            self.CHUNK_OVERLAP = 200
            self.SCRAPING_DELAY = 1.5
            self.SCRAPING_TIMEOUT = 15
            self.MAX_URLS_PER_REQUEST = 20
            self.DEFAULT_SEARCH_LIMIT = 5
            self.MAX_SEARCH_LIMIT = 50
            
            # LLM настройки fallback
            self.OLLAMA_ENABLED = True
            self.OLLAMA_BASE_URL = "http://localhost:11434"
            self.OLLAMA_DEFAULT_MODEL = "llama3:8b"  # ИСПРАВЛЕНО
            self.OLLAMA_FALLBACK_MODELS = ["llama3:latest", "llama3:8b"]  # ИСПРАВЛЕНО
            self.LLM_TEMPERATURE = 0.3
            self.LLM_MAX_TOKENS = 500
            self.LLM_TIMEOUT = 180
            self.MAX_CONTEXT_DOCUMENTS = 3
            self.MAX_CONTEXT_LENGTH = 4000
            self.CONTEXT_TRUNCATE_LENGTH = 1500
            self.LLM_DEMO_MODE = False
            self.LLM_FALLBACK_ENABLED = True
            self.LLM_CACHE_ENABLED = True
            self.LLM_CACHE_TTL = 3600
            self.LLM_CACHE_MAX_SIZE = 100
            self.LLM_RATE_LIMIT = 60
            self.LLM_DAILY_LIMIT = 500
            self.LLM_LOG_REQUESTS = True
            self.SUPPORTED_LANGUAGES = ["en", "uk"]
            self.DEFAULT_LANGUAGE = "en"
            self.SYSTEM_PROMPT_MAX_LENGTH = 1000
            self.USER_PROMPT_MAX_LENGTH = 2000
            
            # Загружаем из переменных окружения
            self._load_from_env()
        
        def _load_from_env(self):
            """Загружает переменные окружения"""
            if os.getenv('USE_CHROMADB'):
                self.USE_CHROMADB = os.getenv('USE_CHROMADB').lower() in ['true', '1', 'yes']
            if os.getenv('LOG_LEVEL'):
                self.LOG_LEVEL = os.getenv('LOG_LEVEL')
            if os.getenv('OLLAMA_ENABLED'):
                self.OLLAMA_ENABLED = os.getenv('OLLAMA_ENABLED').lower() in ['true', '1', 'yes']
            if os.getenv('OLLAMA_BASE_URL'):
                self.OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
            if os.getenv('OLLAMA_DEFAULT_MODEL'):
                self.OLLAMA_DEFAULT_MODEL = os.getenv('OLLAMA_DEFAULT_MODEL')
            if os.getenv('LLM_DEMO_MODE'):
                self.LLM_DEMO_MODE = os.getenv('LLM_DEMO_MODE').lower() in ['true', '1', 'yes']
    
    settings = FallbackSettings()

# ДОБАВЛЕНО: Экспорт API метаданных для совместимости с app/__init__.py
API_METADATA = {
    "title": settings.PROJECT_NAME,
    "version": settings.VERSION,
    "description": settings.DESCRIPTION,
    "contact": {
        "name": "Legal Assistant Team",
        "email": "support@legalassistant.com"
    },
    "license": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
}

# ДОБАВЛЕНО: Экспорт API тегов для совместимости
API_TAGS = [
    {
        "name": "User Chat",
        "description": "User chat endpoints for legal assistance"
    },
    {
        "name": "User Search", 
        "description": "Document search endpoints for users"
    },
    {
        "name": "Admin Documents",
        "description": "Document management endpoints for administrators"
    },
    {
        "name": "Admin Scraper",
        "description": "Web scraping endpoints for administrators"
    },
    {
        "name": "Admin Stats",
        "description": "Statistics and analytics endpoints for administrators"
    },
    {
        "name": "Admin LLM",
        "description": "LLM management and monitoring endpoints"
    },
    {
        "name": "System",
        "description": "System health and information endpoints"
    }
]

# Константы категорий документов
DOCUMENT_CATEGORIES = [
    "general",
    "legislation", 
    "jurisprudence",
    "government",
    "civil_rights",
    "scraped",
    "ukraine_legal",
    "ireland_legal",
    "civil",
    "criminal",
    "tax",
    "corporate",
    "family",
    "labor",
    "real_estate"
]

# Предустановленные юридические сайты
UKRAINE_LEGAL_URLS = [
    "https://zakon.rada.gov.ua/laws/main",
    "https://court.gov.ua/",
    "https://minjust.gov.ua/",
    "https://ccu.gov.ua/",
    "https://npu.gov.ua/"
]

IRELAND_LEGAL_URLS = [
    "https://www.irishimmigration.ie/",
    "https://www.irishstatutebook.ie/",
    "https://www.courts.ie/",
    "https://www.citizensinformation.ie/en/",
    "https://www.justice.ie/",
    "https://www.oireachtas.ie/"
]

# ====================================
# НОВЫЕ КОНСТАНТЫ ДЛЯ LLM
# ====================================

# Рекомендуемые модели Ollama для юридических задач
RECOMMENDED_MODELS = {
    "small": "llama3:8b",         # Быстрая модель 
    "medium": "llama3:latest",    # Балансированная модель (ваша основная)
    "large": "llama3:8b",         # Более точная модель (та же что и small у вас)
    "specialized": "llama3:latest" # Основная модель
}

# Настройки качества ответов
RESPONSE_QUALITY_SETTINGS = {
    "creative": {"temperature": 0.8, "max_tokens": 2000},    # Творческие ответы
    "balanced": {"temperature": 0.5, "max_tokens": 1500},    # Сбалансированные
    "precise": {"temperature": 0.2, "max_tokens": 1000},     # Точные ответы
    "legal": {"temperature": 0.3, "max_tokens": 1500}        # Для юридических вопросов
}

# Лимиты по умолчанию
DEFAULT_LIMITS = {
    "context_documents": 3,
    "context_length": 4000,
    "response_length": 1500,
    "request_timeout": 60
}

# Поддерживаемые языки с метаданными
LANGUAGE_CONFIG = {
    "en": {
        "name": "English",
        "code": "en",
        "rtl": False,
        "supported": True
    },
    "uk": {
        "name": "Українська",
        "code": "uk", 
        "rtl": False,
        "supported": True
    }
}

def get_llm_config() -> dict:
    """Возвращает конфигурацию LLM"""
    return {
        "enabled": settings.OLLAMA_ENABLED,
        "base_url": settings.OLLAMA_BASE_URL,
        "default_model": settings.OLLAMA_DEFAULT_MODEL,
        "fallback_models": settings.OLLAMA_FALLBACK_MODELS,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "timeout": settings.LLM_TIMEOUT,
        "demo_mode": settings.LLM_DEMO_MODE,
        "cache_enabled": settings.LLM_CACHE_ENABLED,
        "supported_languages": settings.SUPPORTED_LANGUAGES,
        "recommended_models": RECOMMENDED_MODELS,
        "quality_settings": RESPONSE_QUALITY_SETTINGS
    }

def validate_llm_config() -> dict:
    """Валидирует конфигурацию LLM"""
    issues = []
    warnings = []
    
    # Проверяем базовые настройки
    if not settings.OLLAMA_ENABLED:
        warnings.append("Ollama disabled in configuration")
    
    if settings.LLM_DEMO_MODE:
        warnings.append("LLM running in demo mode")
    
    if settings.LLM_TEMPERATURE < 0 or settings.LLM_TEMPERATURE > 1:
        issues.append("LLM temperature should be between 0 and 1")
    
    if settings.LLM_MAX_TOKENS < 100:
        issues.append("LLM max_tokens too low (minimum 100)")
    
    if settings.LLM_TIMEOUT < 10:
        warnings.append("LLM timeout very low, may cause request failures")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }