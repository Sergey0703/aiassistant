# ====================================
# ФАЙЛ: backend/models/requests.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для Pydantic моделей запросов
# ====================================

"""
Pydantic модели для входящих запросов
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Dict, Any
from app.config import DOCUMENT_CATEGORIES

class ChatMessage(BaseModel):
    """Модель сообщения чата"""
    message: str = Field(..., min_length=1, max_length=5000, description="Сообщение пользователя")
    language: str = Field(default="en", regex="^(en|uk)$", description="Язык интерфейса")

class SearchRequest(BaseModel):
    """Модель запроса поиска"""
    query: str = Field(..., min_length=1, max_length=1000, description="Поисковый запрос")
    category: Optional[str] = Field(None, description="Фильтр по категории")
    limit: int = Field(default=5, ge=1, le=50, description="Количество результатов")
    
    @validator('category')
    def validate_category(cls, v):
        if v and v not in DOCUMENT_CATEGORIES:
            raise ValueError(f"Category must be one of: {DOCUMENT_CATEGORIES}")
        return v

class DocumentUpload(BaseModel):
    """Модель загрузки документа через текст"""
    filename: str = Field(..., min_length=1, max_length=255, description="Имя файла")
    content: str = Field(..., min_length=10, description="Содержимое документа")
    category: Optional[str] = Field(default="general", description="Категория документа")
    
    @validator('category')
    def validate_category(cls, v):
        if v and v not in DOCUMENT_CATEGORIES:
            raise ValueError(f"Category must be one of: {DOCUMENT_CATEGORIES}")
        return v

class URLScrapeRequest(BaseModel):
    """Модель запроса парсинга URL"""
    url: HttpUrl = Field(..., description="URL для парсинга")
    category: Optional[str] = Field(default="scraped", description="Категория документа")
    selectors: Optional[Dict[str, str]] = Field(None, description="CSS селекторы для парсинга")
    
    @validator('category')
    def validate_category(cls, v):
        if v and v not in DOCUMENT_CATEGORIES:
            raise ValueError(f"Category must be one of: {DOCUMENT_CATEGORIES}")
        return v

class BulkScrapeRequest(BaseModel):
    """Модель запроса массового парсинга"""
    urls: List[str] = Field(..., min_items=1, max_items=20, description="Список URL для парсинга")
    category: str = Field(default="scraped", description="Категория документов")
    delay: float = Field(default=1.0, ge=0.5, le=5.0, description="Задержка между запросами")
    
    @validator('category')
    def validate_category(cls, v):
        if v not in DOCUMENT_CATEGORIES:
            raise ValueError(f"Category must be one of: {DOCUMENT_CATEGORIES}")
        return v
    
    @validator('urls')
    def validate_urls(cls, v):
        if not v:
            raise ValueError("URLs list cannot be empty")
        # Простая валидация URL
        for url in v:
            if not url.strip():
                raise ValueError("URL cannot be empty")
            if not (url.startswith('http://') or url.startswith('https://')):
                raise ValueError(f"Invalid URL format: {url}")
        return [url.strip() for url in v]

class DocumentUpdate(BaseModel):
    """Модель обновления документа"""
    content: Optional[str] = Field(None, min_length=10, description="Новое содержимое")
    category: Optional[str] = Field(None, description="Новая категория")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")
    
    @validator('category')
    def validate_category(cls, v):
        if v and v not in DOCUMENT_CATEGORIES:
            raise ValueError(f"Category must be one of: {DOCUMENT_CATEGORIES}")
        return v

class PredefinedScrapeRequest(BaseModel):
    """Модель запроса парсинга предустановленных сайтов"""
    country: str = Field(..., regex="^(ukraine|ireland)$", description="Страна для парсинга")
    limit: int = Field(default=5, ge=1, le=10, description="Количество сайтов для парсинга")

class ChatHistoryRequest(BaseModel):
    """Модель запроса истории чата"""
    limit: int = Field(default=10, ge=1, le=100, description="Количество последних сообщений")

class FileUploadForm(BaseModel):
    """Модель формы загрузки файла"""
    category: str = Field(default="general", description="Категория документа")
    
    @validator('category')
    def validate_category(cls, v):
        if v not in DOCUMENT_CATEGORIES:
            raise ValueError(f"Category must be one of: {DOCUMENT_CATEGORIES}")
        return v