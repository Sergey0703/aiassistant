# ====================================
# ФАЙЛ: backend/api/admin/documents.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для админских endpoints управления документами
# ====================================

"""
Admin Documents Endpoints - Админские endpoints для управления документами
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import tempfile
import os
import json
import time
import logging
import urllib.parse
import shutil

from models.requests import DocumentUpload, DocumentUpdate
from models.responses import (
    DocumentsResponse, DocumentInfo, DocumentUploadResponse, 
    DocumentDeleteResponse, SuccessResponse
)
from app.dependencies import get_document_service, get_services_status, CHROMADB_ENABLED
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/documents", response_model=DocumentsResponse)
async def get_documents(document_service = Depends(get_document_service)):
    """Получить детальный список всех документов"""
    try:
        if CHROMADB_ENABLED:
            # ChromaDB версия
            logger.info("Using ChromaDB for document retrieval")
            documents = await document_service.get_all_documents()
            
            # Форматируем для фронтенда
            formatted_documents = []
            for doc in documents:
                formatted_doc = DocumentInfo(
                    id=doc["id"],
                    filename=doc["filename"],
                    category=doc["category"],
                    source="ChromaDB",
                    original_url=doc.get("metadata", {}).get("original_url", "N/A"),
                    content=doc["content"],
                    size=doc["size"],
                    word_count=doc["word_count"],
                    chunks_count=doc["chunks_count"],
                    added_at=doc["added_at"],
                    metadata=doc["metadata"]
                )
                formatted_documents.append(formatted_doc)
            
            return DocumentsResponse(
                documents=formatted_documents,
                total=len(formatted_documents),
                message=f"Found {len(formatted_documents)} documents",
                database_type="ChromaDB"
            )
        
        else:
            # SimpleVectorDB версия
            db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
            
            logger.info(f"Using SimpleVectorDB: {db_file}")
            
            if not os.path.exists(db_file):
                return DocumentsResponse(
                    documents=[],
                    total=0,
                    message="No documents database found",
                    database_type="SimpleVectorDB"
                )
            
            with open(db_file, 'r', encoding='utf-8') as f:
                raw_documents = json.load(f)
            
            # Форматируем документы для frontend
            formatted_documents = []
            for doc in raw_documents:
                formatted_doc = DocumentInfo(
                    id=doc["id"],
                    filename=doc["filename"],
                    category=doc["category"],
                    source="SimpleVectorDB",
                    original_url="N/A",
                    content=doc["content"],
                    size=doc["metadata"].get("content_length", len(doc["content"])),
                    word_count=doc["metadata"].get("word_count", 0),
                    chunks_count=len(doc.get("chunks", [])),
                    added_at=doc.get("added_at", time.time()),
                    metadata=doc["metadata"]
                )
                formatted_documents.append(formatted_doc)
            
            # Сортируем по времени добавления (новые первые)
            formatted_documents.sort(key=lambda x: x.added_at, reverse=True)
            
            return DocumentsResponse(
                documents=formatted_documents,
                total=len(formatted_documents),
                message=f"Found {len(formatted_documents)} documents",
                database_type="SimpleVectorDB"
            )
        
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document_file(
    file: UploadFile = File(...),
    category: str = Form("general"),
    document_service = Depends(get_document_service)
):
    """Загрузка документа через файл"""
    try:
        # Проверяем размер файла
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_FILE_SIZE // 1024 // 1024}MB)")
        
        # Проверяем тип файла
        file_extension = os.path.splitext(file.filename or "")[1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed: {settings.ALLOWED_FILE_TYPES}"
            )
        
        # Сохраняем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Обрабатываем и сохраняем в векторную базу
            success = await document_service.process_and_store_file(tmp_file_path, category)
            
            if success:
                logger.info(f"Document uploaded successfully: {file.filename}")
                return DocumentUploadResponse(
                    message="Document uploaded and processed successfully",
                    filename=file.filename or "unknown",
                    category=category,
                    size=len(content),
                    file_type=file.content_type
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to process document")
                
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@router.post("/documents/upload-text", response_model=DocumentUploadResponse)
async def upload_text_document(
    document: DocumentUpload,
    document_service = Depends(get_document_service)
):
    """Загрузка документа через текст"""
    try:
        # Создаем временный файл с текстом
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
            tmp_file.write(document.content)
            tmp_file_path = tmp_file.name
        
        try:
            # Обрабатываем и сохраняем
            success = await document_service.process_and_store_file(
                tmp_file_path, 
                document.category or "general"
            )
            
            if success:
                logger.info(f"Text document uploaded successfully: {document.filename}")
                return DocumentUploadResponse(
                    message="Document uploaded and processed successfully",
                    filename=document.filename,
                    category=document.category or "general",
                    size=len(document.content),
                    file_type="text/plain"
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to process document")
                
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Text upload error: {str(e)}")

@router.delete("/documents/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: str,
    document_service = Depends(get_document_service)
):
    """Удалить документ"""
    try:
        decoded_id = urllib.parse.unquote(doc_id)
        logger.info(f"Attempting to delete document with ID: {decoded_id}")
        
        if CHROMADB_ENABLED:
            # ChromaDB версия
            success = await document_service.delete_document(decoded_id)
            
            if success:
                logger.info(f"Successfully deleted document from ChromaDB: {decoded_id}")
                return DocumentDeleteResponse(
                    message="Document deleted successfully", 
                    deleted_id=decoded_id,
                    database_type="ChromaDB"
                )
            else:
                raise HTTPException(status_code=404, detail=f"Document with ID '{decoded_id}' not found")
        
        else:
            # SimpleVectorDB версия
            db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
            
            if not os.path.exists(db_file):
                raise HTTPException(status_code=404, detail="Database not found")
            
            with open(db_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            original_count = len(documents)
            found_doc = None