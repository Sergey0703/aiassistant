import databases
import sqlalchemy
import os

DATABASE_URL = os.getenv("DB_PATH", "../db/local.sqlite")
database = databases.Database(f"sqlite:///{DATABASE_URL}")

metadata = sqlalchemy.MetaData()

documents = sqlalchemy.Table(
    "documents",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("content", sqlalchemy.Text),
    sqlalchemy.Column("metadata", sqlalchemy.JSON, nullable=True),
)

async def init_db(db_path):
    engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")
    metadata.create_all(engine)
    await database.connect()

async def add_document(content: str, metadata: dict = None):
    query = documents.insert().values(content=content, metadata=metadata)
    return await database.execute(query)

async def query_documents(query_text: str):
    # Пока просто заглушка, позже добавим поиск по векторной БД
    query = documents.select()
    rows = await database.fetch_all(query)
    return [{"id": r["id"], "content": r["content"]} for r in rows]
