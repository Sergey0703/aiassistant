from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Настройка CORS, чтобы React мог обращаться к backend
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # разрешаем запросы с фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Юридичний AI-асистент backend запущен"}


@app.get("/api/ping")
async def ping():
    return {"ping": "pong"}


# Пример загрузки файла (если потребуется)
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    content = await file.read()
    # Пока просто возвращаем имя файла и размер
    return {"filename": file.filename, "size": len(content)}
