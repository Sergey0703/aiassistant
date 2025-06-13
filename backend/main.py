from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Legal Assistant API", version="1.0.0")

# CORS настройка
origins = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class ChatMessage(BaseModel):
    message: str
    language: str = "en"

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None

class DocumentUpload(BaseModel):
    filename: str
    content: str
    category: Optional[str] = None

# Временное хранение (потом заменим на ChromaDB + SQLite)
documents_storage = []
chat_history = []

# === API ENDPOINTS ===

@app.get("/")
async def root():
    return {"message": "Legal Assistant API is running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

# === USER ENDPOINTS ===
@app.post("/api/user/chat", response_model=ChatResponse)
async def chat_with_assistant(message: ChatMessage):
    """Основной endpoint для чата с юридическим ассистентом"""
    try:
        # Временная заглушка для демонстрации
        if message.language == "uk":
            response_text = f"Дякую за ваше питання: '{message.message}'. Це тестова відповідь. Наразі система в розробці."
        else:
            response_text = f"Thank you for your question: '{message.message}'. This is a test response. The system is currently under development."
        
        # Сохраняем в историю
        chat_history.append({
            "message": message.message,
            "response": response_text,
            "language": message.language
        })
        
        return ChatResponse(
            response=response_text,
            sources=["Test Document 1", "Test Document 2"] if len(documents_storage) > 0 else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/chat/history")
async def get_chat_history():
    """Получить историю чата"""
    return {"history": chat_history[-10:]}  # Последние 10 сообщений

# === ADMIN ENDPOINTS ===
@app.post("/api/admin/documents/upload")
async def upload_document(document: DocumentUpload):
    """Загрузка документа в систему"""
    try:
        doc_data = {
            "id": len(documents_storage) + 1,
            "filename": document.filename,
            "content": document.content[:500] + "..." if len(document.content) > 500 else document.content,
            "category": document.category or "general",
            "size": len(document.content)
        }
        documents_storage.append(doc_data)
        
        return {"message": "Document uploaded successfully", "doc_id": doc_data["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/documents")
async def get_documents():
    """Получить список всех документов"""
    return {"documents": documents_storage, "total": len(documents_storage)}

@app.delete("/api/admin/documents/{doc_id}")
async def delete_document(doc_id: int):
    """Удалить документ"""
    global documents_storage
    documents_storage = [doc for doc in documents_storage if doc["id"] != doc_id]
    return {"message": f"Document {doc_id} deleted successfully"}

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Статистика для админ панели"""
    return {
        "total_documents": len(documents_storage),
        "total_chats": len(chat_history),
        "categories": list(set([doc.get("category", "general") for doc in documents_storage]))
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)