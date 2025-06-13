import os
from db import add_document

async def parse_and_store_document(filepath: str):
    # Заглушка: просто считываем текст файла и сохраняем в базу
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    await add_document(content)
