#!/usr/bin/env python3
print("🧪 Проверка пакетов...")

try:
    import fastapi
    print(f"✅ FastAPI {fastapi.__version__}")
    
    import uvicorn  
    print(f"✅ Uvicorn {uvicorn.__version__}")
    
    import pydantic
    print(f"✅ Pydantic {pydantic.VERSION}")
    
    # Пробуем создать приложение
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"message": "Работает!"}
    
    print("✅ FastAPI приложение создано успешно")
    print("\nСоздаем простой сервер...")
    
    # Записываем код сервера
    server_code = '''from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Legal Assistant Test")

@app.get("/")
def read_root():
    return {"message": "Legal Assistant API работает!", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Запуск на http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''
    
    with open("server.py", "w", encoding="utf-8") as f:
        f.write(server_code)
    
    print("✅ Создан server.py")
    print("🚀 Запустите: python server.py")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}")