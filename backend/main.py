# ====================================
# ФАЙЛ: backend/main.py (НОВЫЙ ПОЛНЫЙ ФАЙЛ)
# Заменить весь существующий main.py
# ====================================

"""
Legal Assistant API - Main Application Entry Point
Минимальный launcher для FastAPI приложения
"""

import uvicorn
from app import create_app
from utils.logger import setup_logging

# Настройка логирования
setup_logging()

# Создание приложения
app = create_app()

if __name__ == "__main__":
    print("🏛️ Legal Assistant API v2.0")
    print("📚 Features: Document Processing, Web Scraping, Vector Search")
    print("🌐 Starting server on http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("-" * 50)
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=True  # Включаем reload для разработки
    )