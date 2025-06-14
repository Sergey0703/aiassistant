#!/usr/bin/env python3
"""
Тест для проверки импорта сервисов
"""
import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Python path:", sys.path)

try:
    print("Testing services import...")
    from services.scraper_service import LegalSiteScraper
    print("✅ scraper_service imported successfully")
    
    from services.document_processor import DocumentService
    print("✅ document_processor imported successfully")
    
    # Тест создания объектов
    scraper = LegalSiteScraper()
    doc_service = DocumentService()
    print("✅ Services objects created successfully")
    
    print("🎉 All services working!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTrying to create services manually...")
    
    # Проверяем существование файлов
    files_to_check = [
        "services/__init__.py",
        "services/scraper_service.py", 
        "services/document_processor.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            
except Exception as e:
    print(f"❌ Other error: {e}")

print("\nDirectory structure:")
if os.path.exists("services"):
    for item in os.listdir("services"):
        print(f"  services/{item}")
else:
    print("  services/ directory not found")