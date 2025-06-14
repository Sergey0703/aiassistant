#!/usr/bin/env python3
"""
Отладка базы данных для понимания структуры ID
"""
import json
import os

def debug_database():
    db_file = "simple_db/documents.json"
    
    if not os.path.exists(db_file):
        print("❌ База данных не найдена!")
        return
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        print(f"📊 Всего документов: {len(documents)}")
        print("=" * 60)
        
        for i, doc in enumerate(documents):
            print(f"\n📄 Документ {i+1}:")
            print(f"   ID: {repr(doc['id'])} (тип: {type(doc['id'])})")
            print(f"   Имя файла: {doc['filename']}")
            print(f"   Категория: {doc['category']}")
            
            # Показываем структуру metadata
            if 'metadata' in doc:
                print(f"   Metadata keys: {list(doc['metadata'].keys())}")
                if 'real_scraping' in doc['metadata']:
                    print(f"   Реальный парсинг: {doc['metadata']['real_scraping']}")
            
            print(f"   Размер: {len(doc.get('content', ''))} символов")
            print("-" * 40)
        
        # Показываем уникальные ID
        ids = [doc['id'] for doc in documents]
        print(f"\n🔍 Все ID в базе:")
        for i, doc_id in enumerate(ids):
            print(f"   {i+1}. {repr(doc_id)}")
        
        # Проверяем дубликаты ID
        unique_ids = set(ids)
        if len(unique_ids) != len(ids):
            print(f"\n⚠️ ВНИМАНИЕ: Найдены дублирующиеся ID!")
            print(f"   Уникальных ID: {len(unique_ids)}")
            print(f"   Всего документов: {len(ids)}")
        else:
            print(f"\n✅ Все ID уникальные")
            
    except Exception as e:
        print(f"❌ Ошибка чтения базы: {e}")

def test_delete_simulation(test_id):
    """Симулирует удаление документа"""
    db_file = "simple_db/documents.json"
    
    if not os.path.exists(db_file):
        print("❌ База данных не найдена!")
        return
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        print(f"\n🔍 Тестируем удаление ID: {repr(test_id)}")
        
        # Поиск точного совпадения
        found = False
        for doc in documents:
            if doc['id'] == test_id:
                print(f"✅ Найден документ для удаления: {doc['filename']}")
                found = True
                break
        
        if not found:
            print(f"❌ Документ с ID {repr(test_id)} НЕ НАЙДЕН")
            print("📋 Доступные ID:")
            for doc in documents[:3]:
                print(f"   {repr(doc['id'])}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🔍 Отладка базы данных Legal Assistant")
    print("=" * 60)
    
    debug_database()
    
    # Запрашиваем у пользователя ID для тестирования удаления
    print("\n" + "=" * 60)
    print("🧪 Тест удаления:")
    print("Введите ID документа для тестирования удаления (или Enter для пропуска):")
    
    try:
        test_id = input().strip()
        if test_id:
            test_delete_simulation(test_id)
    except KeyboardInterrupt:
        print("\nВыход...")