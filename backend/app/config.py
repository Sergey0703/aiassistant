# ====================================
# ФАЙЛ: backend/app/config.py (ПОЛНАЯ ВЕРСИЯ)
# Заменить существующий файл полностью
# ====================================

"""
Конфигурация приложения
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
            'DEFAULT_SEARCH_LIMIT': ('DEFAULT_SEARCH_LIMIT', int)
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
            
            # Загружаем из переменных окружения
            self._load_from_env()
        
        def _load_from_env(self):
            """Загружает переменные окружения"""
            if os.getenv('USE_CHROMADB'):
                self.USE_CHROMADB = os.getenv('USE_CHROMADB').lower() in ['true', '1', 'yes']
            if os.getenv('LOG_LEVEL'):
                self.LOG_LEVEL = os.getenv('LOG_LEVEL')
            if os.getenv('MAX_FILE_SIZE'):
                try:
                    self.MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE'))
                except ValueError:
                    pass
    
    settings = FallbackSettings()

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