#!/usr/bin/env python3
"""
Скрипт для проверки содержимого ChromaDB
"""

import sys
import os

# Добавляем текущую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    print("✅ ChromaDB доступен")
    
    # Подключаемся к ChromaDB
    client = chromadb.PersistentClient(path="./chromadb_data")
    print("✅ Подключение к ChromaDB успешно")
    
    # Получаем коллекцию
    try:
        collection = client.get_collection("legal_documents")
        print("✅ Коллекция 'legal_documents' найдена")
        
        # Получаем все документы
        all_docs = collection.get(include=["metadatas", "documents"])
        
        print(f"\n📊 СТАТИСТИКА CHROMADB:")
        print(f"Всего элементов: {len(all_docs['ids'])}")
        
        # Анализируем типы документов
        main_docs = []
        chunks = []
        
        for i, metadata in enumerate(all_docs["metadatas"]):
            if metadata.get("is_chunk", True):
                chunks.append({
                    "id": all_docs["ids"][i],
                    "filename": metadata.get("filename", "Unknown"),
                    "parent_id": metadata.get("parent_document_id", "None")
                })
            else:
                main_docs.append({
                    "id": all_docs["ids"][i], 
                    "filename": metadata.get("filename", "Unknown"),
                    "category": metadata.get("category", "Unknown")
                })
        
        print(f"Основных документов: {len(main_docs)}")
        print(f"Чанков: {len(chunks)}")
        
        print(f"\n📄 ОСНОВНЫЕ ДОКУМЕНТЫ:")
        for i, doc in enumerate(main_docs, 1):
            print(f"{i}. {doc['filename']} (ID: {doc['id'][:20]}...)")
            print(f"   Категория: {doc['category']}")
        
        print(f"\n🧩 ЧАНКИ:")
        chunk_groups = {}
        for chunk in chunks:
            parent = chunk["parent_id"]
            if parent not in chunk_groups:
                chunk_groups[parent] = []
            chunk_groups[parent].append(chunk)
        
        for parent_id, chunk_list in chunk_groups.items():
            if parent_id != "None":
                print(f"Документ {parent_id}: {len(chunk_list)} чанков")
            else:
                print(f"Orphaned chunks: {len(chunk_list)}")
                for chunk in chunk_list:
                    print(f"  - {chunk['filename']} (ID: {chunk['id'][:20]}...)")
        
        # Проверяем несоответствия
        print(f"\n🔍 АНАЛИЗ ПРОБЛЕМ:")
        
        # Есть ли чанки без основного документа?
        orphaned_chunks = [c for c in chunks if c["parent_id"] == "None"]
        if orphaned_chunks:
            print(f"⚠️ Найдено {len(orphaned_chunks)} чанков без основного документа")
        
        # Есть ли основные документы без чанков?
        main_without_chunks = []
        for doc in main_docs:
            has_chunks = any(c["parent_id"] == doc["id"] for c in chunks)
            if not has_chunks:
                main_without_chunks.append(doc)
        
        if main_without_chunks:
            print(f"⚠️ Найдено {len(main_without_chunks)} основных документов без чанков")
        
        # Показываем примеры контента
        print(f"\n📝 ПРИМЕРЫ КОНТЕНТА:")
        for i, doc in enumerate(main_docs[:2], 1):
            doc_index = all_docs["ids"].index(doc["id"])
            content = all_docs["documents"][doc_index]
            print(f"{i}. {doc['filename']}:")
            print(f"   Контент: {content[:100]}...")
            print(f"   Длина: {len(content)} символов")
        
    except Exception as e:
        print(f"❌ Ошибка получения коллекции: {e}")
        
        # Показываем доступные коллекции
        try:
            collections = client.list_collections()
            print(f"Доступные коллекции: {[c.name for c in collections]}")
        except Exception as e2:
            print(f"❌ Ошибка получения списка коллекций: {e2}")

except ImportError:
    print("❌ ChromaDB не установлен")
    print("Установите: pip install chromadb")
except Exception as e:
    print(f"❌ Общая ошибка: {e}")

print(f"\n📁 Проверяем директории:")
if os.path.exists("chromadb_data"):
    print("✅ Папка chromadb_data существует")
    files = os.listdir("chromadb_data")
    print(f"   Файлы: {files}")
else:
    print("❌ Папка chromadb_data не найдена")

if os.path.exists("simple_db"):
    print("✅ Папка simple_db существует")
    if os.path.exists("simple_db/documents.json"):
        print("✅ Файл simple_db/documents.json существует")
        with open("simple_db/documents.json", "r", encoding="utf-8") as f:
            import json
            data = json.load(f)
            print(f"   Документов в simple_db: {len(data)}")
    else:
        print("❌ Файл simple_db/documents.json не найден")
else:
    print("❌ Папка simple_db не найдена")