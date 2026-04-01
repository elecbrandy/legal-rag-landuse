import os
from fastapi import FastAPI, HTTPException
import chromadb
from chromadb.utils import embedding_functions
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# OpenAI 임베딩 설정
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

# ChromaDB 클라이언트 설정
client = chromadb.HttpClient(host='chromadb', port=8000)

class DocumentRequest(BaseModel):
    id: str
    text: str
    metadata: dict = None

@app.get("/")
def health_check():
    return {"status": "Backend is healthy"}

@app.post("/add")
def add_document(req: DocumentRequest):
    try:
        collection = client.get_or_create_collection(
            name="my_docs", 
            embedding_function=openai_ef
        )
        collection.add(
            documents=[req.text],
            metadatas=[req.metadata] if req.metadata else None,
            ids=[req.id]
        )
        return {"message": f"Document {req.id} indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query")
def query_document(text: str, n_results: int = 3):
    try:
        collection = client.get_or_create_collection(
            name="my_docs", 
            embedding_function=openai_ef
        )
        results = collection.query(
            query_texts=[text],
            n_results=n_results
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))