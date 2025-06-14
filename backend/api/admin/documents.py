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
from typing import Optional, List

from models.requests import DocumentUpload, DocumentUpdate
from models.responses import (
    DocumentsResponse, DocumentInfo, DocumentUploadResponse, 
    DocumentDeleteResponse, SuccessResponse
)
from app.dependencies import get_document_service, get_services_status, CHROMADB_ENABLED
from app.config import settings, DOCUMENT_CATEGORIES

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/documents", response_model=DocumentsResponse)
async def get_documents(
    category: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
    document_service = Depends(get_document_service)
):
    """Получить детальный список всех документов с фильтрацией"""
    try:
        logger.info(f"Getting documents with category={category}, limit={limit}, offset={offset}")
        
        if CHROMADB_ENABLED:
            # ChromaDB версия
            logger.info("Using ChromaDB for document retrieval")
            documents = await document_service.get_all_documents()
            
            # Фильтрация по категории
            if category and category != "all":
                documents = [doc for doc in documents if doc.get("category") == category]
            
            # Пагинация
            total_documents = len(documents)
            if limit:
                end_index = offset + limit
                documents = documents[offset:end_index]
            
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
                total=total_documents,
                message=f"Found {len(formatted_documents)} documents (showing {len(formatted_documents)} of {total_documents})",
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
            
            # Фильтрация по категории
            if category and category != "all":
                raw_documents = [doc for doc in raw_documents if doc.get("category") == category]
            
            # Сортируем по времени добавления (новые первые)
            raw_documents.sort(key=lambda x: x.get("added_at", 0), reverse=True)
            
            total_documents = len(raw_documents)
            
            # Пагинация
            if limit:
                end_index = offset + limit
                raw_documents = raw_documents[offset:end_index]
            
            # Форматируем документы для frontend
            formatted_documents = []
            for doc in raw_documents:
                # Определяем источник по метаданным
                source = _determine_document_source(doc)
                original_url = _extract_original_url(doc)
                
                formatted_doc = DocumentInfo(
                    id=doc["id"],
                    filename=doc["filename"],
                    category=doc["category"],
                    source=source,
                    original_url=original_url,
                    content=doc["content"],
                    size=doc["metadata"].get("content_length", len(doc["content"])),
                    word_count=doc["metadata"].get("word_count", 0),
                    chunks_count=len(doc.get("chunks", [])),
                    added_at=doc.get("added_at", time.time()),
                    metadata=doc["metadata"]
                )
                formatted_documents.append(formatted_doc)
            
            return DocumentsResponse(
                documents=formatted_documents,
                total=total_documents,
                message=f"Found {len(formatted_documents)} documents (showing {len(formatted_documents)} of {total_documents})",
                database_type="SimpleVectorDB"
            )
        
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@router.get("/documents/{doc_id}")
async def get_document_by_id(
    doc_id: str,
    document_service = Depends(get_document_service)
):
    """Получить конкретный документ по ID"""
    try:
        decoded_id = urllib.parse.unquote(doc_id)
        logger.info(f"Getting document by ID: {decoded_id}")
        
        if CHROMADB_ENABLED:
            # ChromaDB версия
            documents = await document_service.get_all_documents()
            document = next((doc for doc in documents if doc["id"] == decoded_id), None)
            
            if not document:
                raise HTTPException(status_code=404, detail=f"Document with ID '{decoded_id}' not found")
            
            return DocumentInfo(
                id=document["id"],
                filename=document["filename"],
                category=document["category"],
                source="ChromaDB",
                original_url=document.get("metadata", {}).get("original_url", "N/A"),
                content=document["content"],
                size=document["size"],
                word_count=document["word_count"],
                chunks_count=document["chunks_count"],
                added_at=document["added_at"],
                metadata=document["metadata"]
            )
        else:
            # SimpleVectorDB версия
            db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
            
            if not os.path.exists(db_file):
                raise HTTPException(status_code=404, detail="Database not found")
            
            with open(db_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            document = next((doc for doc in documents if doc["id"] == decoded_id), None)
            
            if not document:
                raise HTTPException(status_code=404, detail=f"Document with ID '{decoded_id}' not found")
            
            source = _determine_document_source(document)
            original_url = _extract_original_url(document)
            
            return DocumentInfo(
                id=document["id"],
                filename=document["filename"],
                category=document["category"],
                source=source,
                original_url=original_url,
                content=document["content"],
                size=document["metadata"].get("content_length", len(document["content"])),
                word_count=document["metadata"].get("word_count", 0),
                chunks_count=len(document.get("chunks", [])),
                added_at=document.get("added_at", time.time()),
                metadata=document["metadata"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document by ID error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document_file(
    file: UploadFile = File(...),
    category: str = Form("general"),
    document_service = Depends(get_document_service)
):
    """Загрузка документа через файл"""
    try:
        logger.info(f"Uploading file: {file.filename}, category: {category}")
        
        # Валидация категории
        if category not in DOCUMENT_CATEGORIES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid category. Allowed: {DOCUMENT_CATEGORIES}"
            )
        
        # Проверяем размер файла
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large (max {settings.MAX_FILE_SIZE // 1024 // 1024}MB)"
            )
        
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
        logger.info(f"Uploading text document: {document.filename}")
        
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

@router.put("/documents/{doc_id}", response_model=SuccessResponse)
async def update_document(
    doc_id: str,
    update_data: DocumentUpdate,
    document_service = Depends(get_document_service)
):
    """Обновить документ"""
    try:
        decoded_id = urllib.parse.unquote(doc_id)
        logger.info(f"Updating document: {decoded_id}")
        
        if CHROMADB_ENABLED:
            # ChromaDB версия обновления
            success = await document_service.update_document(
                decoded_id, 
                update_data.content, 
                update_data.metadata
            )
            
            if success:
                return SuccessResponse(
                    message=f"Document '{decoded_id}' updated successfully",
                    data={"updated_id": decoded_id}
                )
            else:
                raise HTTPException(status_code=404, detail="Document not found or update failed")
        else:
            # SimpleVectorDB версия - более сложная логика обновления
            db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
            
            if not os.path.exists(db_file):
                raise HTTPException(status_code=404, detail="Database not found")
            
            with open(db_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            # Находим документ
            doc_index = None
            for i, doc in enumerate(documents):
                if doc["id"] == decoded_id:
                    doc_index = i
                    break
            
            if doc_index is None:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Обновляем поля
            if update_data.content:
                documents[doc_index]["content"] = update_data.content
                documents[doc_index]["metadata"]["content_length"] = len(update_data.content)
                documents[doc_index]["metadata"]["word_count"] = len(update_data.content.split())
                documents[doc_index]["metadata"]["updated_at"] = time.time()
            
            if update_data.category:
                documents[doc_index]["category"] = update_data.category
            
            if update_data.metadata:
                documents[doc_index]["metadata"].update(update_data.metadata)
            
            # Сохраняем
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            
            return SuccessResponse(
                message=f"Document '{decoded_id}' updated successfully",
                data={"updated_id": decoded_id}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update error: {e}")
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

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
            
            # Поиск по точному совпадению ID
            for doc in documents:
                if doc['id'] == decoded_id:
                    found_doc = doc
                    break
            
            if not found_doc:
                logger.warning(f"Document not found with ID: {decoded_id}")
                logger.info(f"Available document IDs: {[doc['id'] for doc in documents[:3]]}")
                raise HTTPException(status_code=404, detail=f"Document with ID '{decoded_id}' not found")
            
            # Удаляем найденный документ
            documents = [doc for doc in documents if doc['id'] != decoded_id]
            
            # Сохраняем обновленный список
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            
            deleted_count = original_count - len(documents)
            logger.info(f"Successfully deleted document: {found_doc['filename']}")
            
            return DocumentDeleteResponse(
                message=f"Document '{found_doc['filename']}' deleted successfully",
                deleted_id=decoded_id,
                deleted_count=deleted_count,
                remaining_documents=len(documents),
                database_type="SimpleVectorDB"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

@router.delete("/documents", response_model=SuccessResponse)
async def delete_multiple_documents(
    document_ids: List[str],
    document_service = Depends(get_document_service)
):
    """Удалить несколько документов"""
    try:
        if not document_ids:
            raise HTTPException(status_code=400, detail="No document IDs provided")
        
        if len(document_ids) > 50:
            raise HTTPException(status_code=400, detail="Cannot delete more than 50 documents at once")
        
        logger.info(f"Deleting {len(document_ids)} documents")
        
        deleted_count = 0
        failed_ids = []
        
        for doc_id in document_ids:
            try:
                decoded_id = urllib.parse.unquote(doc_id)
                success = await document_service.delete_document(decoded_id)
                if success:
                    deleted_count += 1
                else:
                    failed_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Failed to delete document {doc_id}: {e}")
                failed_ids.append(doc_id)
        
        message = f"Successfully deleted {deleted_count}/{len(document_ids)} documents"
        if failed_ids:
            message += f". Failed to delete: {failed_ids}"
        
        return SuccessResponse(
            message=message,
            data={
                "deleted_count": deleted_count,
                "failed_count": len(failed_ids),
                "failed_ids": failed_ids
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk delete error: {str(e)}")

@router.get("/documents/categories")
async def get_document_categories(
    document_service = Depends(get_document_service)
):
    """Получить список категорий документов с количеством"""
    try:
        # Получаем статистику
        stats = await document_service.get_stats()
        actual_categories = stats.get('categories', [])
        
        # Подсчитываем документы по категориям
        category_counts = {}
        
        if CHROMADB_ENABLED:
            documents = await document_service.get_all_documents()
            for doc in documents:
                category = doc.get("category", "general")
                category_counts[category] = category_counts.get(category, 0) + 1
        else:
            db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
            if os.path.exists(db_file):
                with open(db_file, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                
                for doc in documents:
                    category = doc.get("category", "general")
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        # Формируем ответ
        categories_info = []
        for category in DOCUMENT_CATEGORIES:
            count = category_counts.get(category, 0)
            categories_info.append({
                "name": category,
                "count": count,
                "active": count > 0
            })
        
        return {
            "categories": categories_info,
            "total_categories": len(categories_info),
            "active_categories": len([c for c in categories_info if c["active"]]),
            "total_documents": sum(category_counts.values())
        }
        
    except Exception as e:
        logger.error(f"Get categories error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.post("/documents/backup")
async def backup_documents(
    document_service = Depends(get_document_service)
):
    """Создать резервную копию документов"""
    try:
        backup_filename = f"documents_backup_{int(time.time())}.json"
        backup_path = os.path.join("backups", backup_filename)
        
        # Создаем папку для бэкапов
        os.makedirs("backups", exist_ok=True)
        
        if CHROMADB_ENABLED:
            documents = await document_service.get_all_documents()
        else:
            db_file = os.path.join(document_service.vector_db.persist_directory, "documents.json")
            if os.path.exists(db_file):
                with open(db_file, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
            else:
                documents = []
        
        # Сохраняем бэкап
        backup_data = {
            "created_at": time.time(),
            "total_documents": len(documents),
            "database_type": "ChromaDB" if CHROMADB_ENABLED else "SimpleVectorDB",
            "documents": documents
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Backup created: {backup_path}")
        
        return SuccessResponse(
            message=f"Backup created successfully",
            data={
                "backup_file": backup_filename,
                "backup_path": backup_path,
                "documents_count": len(documents),
                "size_bytes": os.path.getsize(backup_path)
            }
        )
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Backup error: {str(e)}")

# Utility functions

def _determine_document_source(doc: dict) -> str:
    """Определяет источник документа по метаданным"""
    metadata = doc.get("metadata", {})
    category = doc.get("category", "")
    
    if metadata.get("scraped_at"):
        return "Web Scraping"
    elif category == "ukraine_legal":
        return "Ukraine Legal Sites"
    elif category == "ireland_legal":
        return "Ireland Legal Sites"
    elif category == "scraped":
        return "Manual URL Scraping"
    elif metadata.get("file_extension"):
        return "File Upload"
    else:
        return "Unknown"

def _extract_original_url(doc: dict) -> str:
    """Извлекает оригинальный URL из документа"""
    metadata = doc.get("metadata", {})
    content = doc.get("content", "")
    
    # Проверяем метаданные
    if metadata.get("url"):
        return metadata["url"]
    
    # Ищем в контенте
    if "URL:" in content:
        url_lines = [line for line in content.split('\n') if line.startswith('URL:')]
        if url_lines:
            return url_lines[0].replace('URL:', '').strip()
    
    return "N/A"