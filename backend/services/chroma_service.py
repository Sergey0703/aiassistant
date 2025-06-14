# ====================================
# ФАЙЛ: backend/services/chroma_service.py (НОВЫЙ ФАЙЛ)
# Создать новый файл для работы с ChromaDB
# ====================================

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import logging
import time
import hashlib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class ProcessedDocument:
    id: str
    filename: str
    content: str
    metadata: Dict
    category: str
    chunks: List[str]

class ChromaDBService:
    """Сервис для работы с ChromaDB векторной базой данных"""
    
    def __init__(self, persist_directory: str = "./chromadb_data"):
        self.persist_directory = persist_directory
        
        # Создаем директорию если не существует
        os.makedirs(persist_directory, exist_ok=True)
        
        # Инициализируем ChromaDB клиент
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Настраиваем эмбеддинг функцию (можно поменять на OpenAI или другую)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  # Быстрая и качественная модель
        )
        
        # Создаем или получаем коллекцию документов
        self.collection = self.client.get_or_create_collection(
            name="legal_documents",
            embedding_function=self.embedding_function,
            metadata={"description": "Legal Assistant Documents Collection"}
        )
        
        logger.info(f"ChromaDB initialized with {self.collection.count()} documents")
    
    async def add_document(self, document: ProcessedDocument) -> bool:
        """Добавляет документ в ChromaDB"""
        try:
            # Подготавливаем метаданные для ChromaDB
            chroma_metadata = {
                "filename": document.filename,
                "category": document.category,
                "content_length": len(document.content),
                "word_count": len(document.content.split()),
                "chunks_count": len(document.chunks),
                "added_at": time.time(),
                **document.metadata  # Добавляем оригинальные метаданные
            }
            
            # Если документ большой, разбиваем на чанки
            if len(document.chunks) > 1:
                # Добавляем каждый чанк как отдельный документ
                chunk_ids = []
                chunk_documents = []
                chunk_metadatas = []
                
                for i, chunk in enumerate(document.chunks):
                    chunk_id = f"{document.id}_chunk_{i}"
                    chunk_ids.append(chunk_id)
                    chunk_documents.append(chunk)
                    
                    chunk_metadata = chroma_metadata.copy()
                    chunk_metadata.update({
                        "chunk_index": i,
                        "parent_document_id": document.id,
                        "is_chunk": True
                    })
                    chunk_metadatas.append(chunk_metadata)
                
                # Добавляем все чанки одним запросом
                self.collection.add(
                    ids=chunk_ids,
                    documents=chunk_documents,
                    metadatas=chunk_metadatas
                )
                
                logger.info(f"Added document {document.filename} as {len(document.chunks)} chunks")
            else:
                # Добавляем как один документ
                chroma_metadata["is_chunk"] = False
                
                self.collection.add(
                    ids=[document.id],
                    documents=[document.content],
                    metadatas=[chroma_metadata]
                )
                
                logger.info(f"Added document {document.filename} as single document")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to ChromaDB: {str(e)}")
            return False
    
    async def search_documents(self, query: str, n_results: int = 5, 
                             category: str = None, **filters) -> List[Dict]:
        """Поиск документов по семантическому сходству"""
        try:
            # Подготавливаем фильтры
            where_filter = {}
            
            if category:
                where_filter["category"] = category
            
            # Добавляем дополнительные фильтры
            where_filter.update(filters)
            
            # Выполняем поиск
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Форматируем результаты
            formatted_results = []
            
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    result = {
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "relevance_score": 1 - results["distances"][0][i],  # Преобразуем distance в score
                        "document_id": results["metadatas"][0][i].get("parent_document_id") or results["ids"][0][i],
                        "filename": results["metadatas"][0][i].get("filename", "Unknown")
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def get_document_count(self) -> int:
        """Возвращает количество документов в коллекции"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0
    
    async def delete_document(self, document_id: str) -> bool:
        """Удаляет документ и все его чанки"""
        try:
            # Сначала находим все чанки этого документа
            results = self.collection.get(
                where={"parent_document_id": document_id},
                include=["metadatas"]
            )
            
            ids_to_delete = []
            
            # Добавляем ID чанков
            if results["ids"]:
                ids_to_delete.extend(results["ids"])
            
            # Добавляем основной документ
            ids_to_delete.append(document_id)
            
            # Удаляем все найденные документы
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted document {document_id} and {len(ids_to_delete)-1} chunks")
                return True
            else:
                logger.warning(f"Document {document_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    async def get_all_documents(self) -> List[Dict]:
        """Получает все документы для админ панели"""
        try:
            # Получаем только основные документы (не чанки)
            results = self.collection.get(
                where={"is_chunk": False},
                include=["documents", "metadatas"]
            )
            
            documents = []
            
            if results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i]
                    
                    doc = {
                        "id": doc_id,
                        "filename": metadata.get("filename", "Unknown"),
                        "category": metadata.get("category", "general"),
                        "content": results["documents"][i],
                        "size": metadata.get("content_length", 0),
                        "word_count": metadata.get("word_count", 0),
                        "chunks_count": metadata.get("chunks_count", 1),
                        "added_at": metadata.get("added_at", time.time()),
                        "metadata": metadata
                    }
                    documents.append(doc)
            
            # Сортируем по дате добавления (новые первые)
            documents.sort(key=lambda x: x["added_at"], reverse=True)
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting all documents: {str(e)}")
            return []
    
    async def update_document(self, document_id: str, new_content: str = None, 
                            new_metadata: Dict = None) -> bool:
        """Обновляет документ"""
        try:
            # ChromaDB не поддерживает прямое обновление, поэтому удаляем и добавляем заново
            if new_content or new_metadata:
                # Получаем текущий документ
                current = self.collection.get(
                    ids=[document_id],
                    include=["documents", "metadatas"]
                )
                
                if not current["ids"]:
                    return False
                
                # Подготавливаем новые данные
                content = new_content if new_content else current["documents"][0]
                metadata = current["metadatas"][0].copy()
                
                if new_metadata:
                    metadata.update(new_metadata)
                
                # Удаляем старый
                await self.delete_document(document_id)
                
                # Добавляем новый
                self.collection.add(
                    ids=[document_id],
                    documents=[content],
                    metadatas=[metadata]
                )
                
                logger.info(f"Updated document {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False
    
    async def get_stats(self) -> Dict:
        """Получает статистику базы данных"""
        try:
            total_count = await self.get_document_count()
            
            # Получаем уникальные категории
            all_results = self.collection.get(
                where={"is_chunk": False},
                include=["metadatas"]
            )
            
            categories = set()
            if all_results["metadatas"]:
                categories = set(meta.get("category", "general") for meta in all_results["metadatas"])
            
            return {
                "total_documents": total_count,
                "categories": list(categories),
                "database_type": "ChromaDB",
                "persist_directory": self.persist_directory,
                "embedding_model": "all-MiniLM-L6-v2"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {
                "total_documents": 0,
                "categories": [],
                "error": str(e)
            }

# Для обратной совместимости
class DocumentProcessor:
    """Обработчик документов - остается тот же"""
    
    def __init__(self):
        self.supported_formats = {
            '.txt': self._process_txt,
            '.md': self._process_txt,
        }
    
    async def process_file(self, file_path: str, category: str = "general") -> Optional[ProcessedDocument]:
        """Обрабатывает файл и извлекает текст"""
        try:
            from pathlib import Path
            
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            if extension not in self.supported_formats:
                content = await self._process_txt(file_path)
            else:
                content = await self.supported_formats[extension](file_path)
            
            if not content or len(content.strip()) < 10:
                logger.warning(f"No meaningful content extracted from {file_path.name}")
                return None
            
            # Создаем метаданные
            metadata = await self._extract_metadata(file_path, content)
            
            # Разбиваем на чанки
            chunks = self._chunk_text(content)
            
            # Создаем ID документа
            doc_id = self._generate_doc_id(file_path.name, content)
            
            return ProcessedDocument(
                id=doc_id,
                filename=file_path.name,
                content=content,
                metadata=metadata,
                category=category,
                chunks=chunks
            )
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return None
    
    async def _process_txt(self, file_path) -> str:
        """Обрабатывает текстовые файлы"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            for encoding in ['cp1251', 'iso-8859-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except:
                    continue
            logger.error(f"Could not decode text file {file_path}")
            return ""
    
    async def _extract_metadata(self, file_path, content: str) -> Dict:
        """Извлекает метаданные документа"""
        return {
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_extension": file_path.suffix,
            "content_length": len(content),
            "word_count": len(content.split()),
            "created_at": file_path.stat().st_ctime,
            "modified_at": file_path.stat().st_mtime,
            "processed_at": time.time()
        }
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Разбивает текст на чанки"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end)
                )
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def _generate_doc_id(self, filename: str, content: str) -> str:
        """Генерирует уникальный ID для документа"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{filename}_{content_hash}"

class DocumentService:
    """Основной сервис документов с ChromaDB"""
    
    def __init__(self, db_path: str = "./chromadb_data"):
        self.processor = DocumentProcessor()
        self.vector_db = ChromaDBService(db_path)
    
    async def process_and_store_file(self, file_path: str, category: str = "general") -> bool:
        """Обрабатывает файл и сохраняет в ChromaDB"""
        document = await self.processor.process_file(file_path, category)
        
        if not document:
            return False
        
        return await self.vector_db.add_document(document)
    
    async def search(self, query: str, category: str = None, limit: int = 5) -> List[Dict]:
        """Поиск документов"""
        return await self.vector_db.search_documents(query, limit, category)
    
    async def get_stats(self) -> Dict:
        """Получает статистику"""
        return await self.vector_db.get_stats()
    
    async def get_all_documents(self) -> List[Dict]:
        """Получает все документы"""
        return await self.vector_db.get_all_documents()
    
    async def delete_document(self, document_id: str) -> bool:
        """Удаляет документ"""
        return await self.vector_db.delete_document(document_id)