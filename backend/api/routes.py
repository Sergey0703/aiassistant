from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"ping": "pong"}

@router.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    content = await file.read()
    return {"filename": file.filename, "size": len(content)}
