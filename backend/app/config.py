# ====================================
# ФАЙЛ: backend/app/config.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для конфигурации
# ====================================

"""
Конфигурация приложения
"""

from pydantic_settings import BaseSettings
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создаем глобальный экземпляр настроек
settings = Settings()

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
    "https://www.irishstatutebook.ie/",
    "https://www.courts.ie/",
    "https://www.citizensinformation.ie/en/",
    "https://www.justice.ie/",
    "https://www.oireachtas.ie/"
]