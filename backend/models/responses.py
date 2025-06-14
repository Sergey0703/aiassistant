# ====================================
# ФАЙЛ: backend/models/responses.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для Pydantic моделей ответов
# ====================================

"""
Pydantic модели для исходящих ответов
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class ChatResponse(BaseModel):
    """Модель ответа чата"""
    response: str = Field(..., description="Ответ ассистента")
    sources: Optional[List[str]] = Field(None, description="Источники информации")

class SearchResult(BaseModel):
    """Модель результата поиска"""
    content: str = Field(..., description="Содержимое документа или фрагмента")
    filename: str = Field(..., description="Имя файла")
    document_id: str = Field(..., description="ID документа")
    relevance_score: float = Field(..., ge=0, le=1, description="Оценка релевантности")
    metadata: Dict[str, Any] = Field(..., description="Метаданные документа")

class SearchResponse(BaseModel):
    """Модель ответа поиска"""
    query: str = Field(..., description="Поисковый запрос")
    results: List[SearchResult] = Field(..., description="Результаты поиска")
    total_found: int = Field(..., ge=0, description="Общее количество найденных результатов")
    search_metadata: Dict[str, Any] = Field(..., description="Метаданные поиска")

class DocumentInfo(BaseModel):
    """Модель информации о документе"""
    id: Union[str, int] = Field(..., description="ID документа")
    filename: str = Field(..., description="Имя файла")
    category: str = Field(..., description="Категория документа")
    source: str = Field(..., description="Источник документа")
    original_url: str = Field(default="N/A", description="Оригинальный URL")
    content: str = Field(..., description="Содержимое документа")
    size: int = Field(..., ge=0, description="Размер в байтах")
    word_count: int = Field(default=0, ge=0, description="Количество слов")
    chunks_count: int = Field(default=1, ge=1, description="Количество чанков")
    added_at: float = Field(..., description="Время добавления (Unix timestamp)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")

class DocumentsResponse(BaseModel):
    """Модель ответа со списком документов"""
    documents: List[DocumentInfo] = Field(..., description="Список документов")
    total: int = Field(..., ge=0, description="Общее количество документов")
    message: Optional[str] = Field(None, description="Дополнительное сообщение")
    database_type: Optional[str] = Field(None, description="Тип используемой базы данных")

class DocumentUploadResponse(BaseModel):
    """Модель ответа загрузки документа"""
    message: str = Field(..., description="Сообщение о результате")
    filename: str = Field(..., description="Имя загруженного файла")
    category: str = Field(..., description="Категория документа")
    size: int = Field(..., ge=0, description="Размер файла")
    file_type: Optional[str] = Field(None, description="Тип файла")

class DocumentDeleteResponse(BaseModel):
    """Модель ответа удаления документа"""
    message: str = Field(..., description="Сообщение о результате")
    deleted_id: Union[str, int] = Field(..., description="ID удаленного документа")
    deleted_count: Optional[int] = Field(None, description="Количество удаленных элементов")
    remaining_documents: Optional[int] = Field(None, description="Оставшееся количество документов")
    database_type: Optional[str] = Field(None, description="Тип базы данных")

class ScrapeResult(BaseModel):
    """Модель результата парсинга одного URL"""
    url: str = Field(..., description="Обработанный URL")
    title: str = Field(..., description="Заголовок документа")
    success: bool = Field(..., description="Успешность парсинга")
    content_length: int = Field(default=0, ge=0, description="Длина контента")
    error: Optional[str] = Field(None, description="Ошибка парсинга")

class ScrapeResponse(BaseModel):
    """Модель ответа парсинга"""
    message: str = Field(..., description="Общее сообщение о результате")
    results: List[ScrapeResult] = Field(..., description="Результаты парсинга")
    summary: Dict[str, Any] = Field(..., description="Сводка результатов")

class AdminStats(BaseModel):
    """Модель статистики админ панели"""
    total_documents: int = Field(..., ge=0, description="Общее количество документов")
    total_chats: int = Field(..., ge=0, description="Общее количество чатов")
    categories: List[str] = Field(..., description="Список категорий")
    services_status: Dict[str, bool] = Field(..., description="Статус сервисов")
    database_type: Optional[str] = Field(None, description="Тип базы данных")
    vector_db_info: Optional[Dict[str, Any]] = Field(None, description="Информация о векторной БД")

class ChatHistoryItem(BaseModel):
    """Модель элемента истории чата"""
    message: str = Field(..., description="Сообщение пользователя")
    response: str = Field(..., description="Ответ ассистента")
    language: str = Field(..., description="Язык")
    sources: Optional[List[str]] = Field(None, description="Источники")
    timestamp: Optional[float] = Field(None, description="Время сообщения")

class ChatHistoryResponse(BaseModel):
    """Модель ответа истории чатов"""
    history: List[ChatHistoryItem] = Field(..., description="История чатов")
    total_messages: int = Field(..., ge=0, description="Общее количество сообщений")

class HealthCheckResponse(BaseModel):
    """Модель ответа проверки здоровья системы"""
    status: str = Field(..., description="Статус системы")
    services: Dict[str, bool] = Field(..., description="Статус сервисов")
    vector_db: Optional[Dict[str, Any]] = Field(None, description="Информация о векторной БД")
    vector_db_error: Optional[str] = Field(None, description="Ошибка векторной БД")

class PredefinedSitesResponse(BaseModel):
    """Модель ответа предустановленных сайтов"""
    ukraine: List[str] = Field(..., description="Украинские юридические сайты")
    ireland: List[str] = Field(..., description="Ирландские юридические сайты")
    total: Dict[str, int] = Field(..., description="Количество сайтов по странам")

class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой"""
    detail: str = Field(..., description="Описание ошибки")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время ошибки")

class SuccessResponse(BaseModel):
    """Модель успешного ответа"""
    message: str = Field(..., description="Сообщение об успехе")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")

class NotificationResponse(BaseModel):
    """Модель уведомления"""
    message: str = Field(..., description="Текст уведомления")
    type: str = Field(..., regex="^(success|error|info|warning)$", description="Тип уведомления")
    duration: Optional[int] = Field(None, description="Длительность показа в миллисекундах")