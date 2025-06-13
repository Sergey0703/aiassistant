"""
Простая версия document processor без ChromaDB
"""
import asyncio
from typing import List, Dict, Optional
import tempfile
import os
from pathlib import Path
import logging
from dataclasses import dataclass
import hashlib
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessedDocument:
    id: str
    filename: str
    content: str
    metadata: Dict
    category: str
    chunks: List[str]

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = {
            '.txt': self._process_txt,
            '.md': self._process_txt,
        }
    
    async def process_file(self, file_path: str, category: str = "general") -> Optional[ProcessedDocument]:
        """Обрабатывает файл и извлекает текст"""
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            if extension not in self.supported_formats:
                # Пробуем как текстовый файл
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
    
    async def _process_txt(self, file_path: Path) -> str:
        """Обрабатывает текстовые файлы"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Пробуем другие кодировки
            for encoding in ['cp1251', 'iso-8859-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except:
                    continue
            logger.error(f"Could not decode text file {file_path}")
            return ""
    
    async def _extract_metadata(self, file_path: Path, content: str) -> Dict:
        """Извлекает метаданные документа"""
        metadata = {
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_extension": file_path.suffix,
            "content_length": len(content),
            "word_count": len(content.split()),
            "created_at": file_path.stat().st_ctime,
            "modified_at": file_path.stat().st_mtime,
            "language": "unknown",
            "processed_at": time.time()
        }
        
        return metadata
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Разбивает текст на чанки"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                # Ищем ближайший разрыв предложения
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

class SimpleVectorDB:
    """Простая база данных в памяти вместо ChromaDB"""
    
    def __init__(self, persist_directory: str = "./simple_db"):
        self.persist_directory = persist_directory
        self.documents = []
        self.metadata_file = os.path.join(persist_directory, "documents.json")
        
        # Создаем папку если не существует
        os.makedirs(persist_directory, exist_ok=True)
        
        # Загружаем существующие документы
        self._load_documents()
    
    def _load_documents(self):
        """Загружает документы из файла"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded {len(self.documents)} documents from storage")
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.documents = []
    
    def _save_documents(self):
        """Сохраняет документы в файл"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
    
    async def add_document(self, document: ProcessedDocument) -> bool:
        """Добавляет документ в базу"""
        try:
            # Преобразуем в словарь для сохранения
            doc_dict = {
                "id": document.id,
                "filename": document.filename,
                "content": document.content,
                "metadata": document.metadata,
                "category": document.category,
                "chunks": document.chunks,
                "added_at": time.time()
            }
            
            # Проверяем, не существует ли уже такой документ
            existing_ids = [doc["id"] for doc in self.documents]
            if document.id in existing_ids:
                logger.warning(f"Document {document.id} already exists, updating...")
                # Обновляем существующий
                for i, doc in enumerate(self.documents):
                    if doc["id"] == document.id:
                        self.documents[i] = doc_dict
                        break
            else:
                # Добавляем новый
                self.documents.append(doc_dict)
            
            self._save_documents()
            logger.info(f"Added document {document.filename} with {len(document.chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return False
    
    async def search_documents(self, query: str, n_results: int = 5, category: str = None) -> List[Dict]:
        """Простой поиск по ключевым словам"""
        try:
            query_words = query.lower().split()
            results = []
            
            for doc in self.documents:
                if category and doc["category"] != category:
                    continue
                
                # Простой поиск по содержимому
                content_lower = doc["content"].lower()
                score = 0
                
                for word in query_words:
                    if word in content_lower:
                        score += content_lower.count(word)
                
                if score > 0:
                    # Находим лучший чанк
                    best_chunk = ""
                    best_chunk_score = 0
                    
                    for chunk in doc["chunks"]:
                        chunk_lower = chunk.lower()
                        chunk_score = sum(chunk_lower.count(word) for word in query_words)
                        if chunk_score > best_chunk_score:
                            best_chunk_score = chunk_score
                            best_chunk = chunk
                    
                    results.append({
                        "content": best_chunk or doc["content"][:500],
                        "metadata": doc["metadata"],
                        "relevance_score": score / len(query_words),
                        "document_id": doc["id"],
                        "filename": doc["filename"]
                    })
            
            # Сортируем по релевантности
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return results[:n_results]
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def get_document_count(self) -> int:
        """Возвращает количество документов"""
        return len(self.documents)
    
    async def delete_document(self, document_id: str) -> bool:
        """Удаляет документ"""
        try:
            initial_count = len(self.documents)
            self.documents = [doc for doc in self.documents if doc["id"] != document_id]
            
            if len(self.documents) < initial_count:
                self._save_documents()
                logger.info(f"Deleted document {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

class DocumentService:
    """Простой сервис обработки документов"""
    
    def __init__(self, db_path: str = "./simple_db"):
        self.processor = DocumentProcessor()
        self.vector_db = SimpleVectorDB(db_path)
    
    async def process_and_store_file(self, file_path: str, category: str = "general") -> bool:
        """Обрабатывает файл и сохраняет в базу"""
        document = await self.processor.process_file(file_path, category)
        
        if not document:
            return False
        
        return await self.vector_db.add_document(document)
    
    async def search(self, query: str, category: str = None, limit: int = 5) -> List[Dict]:
        """Поиск документов"""
        return await self.vector_db.search_documents(query, limit, category)
    
    async def get_stats(self) -> Dict:
        """Получает статистику"""
        return {
            "total_documents": await self.vector_db.get_document_count(),
            "db_path": self.vector_db.persist_directory
        }