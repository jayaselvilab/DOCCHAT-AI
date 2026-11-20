"""FastAPI app: REST endpoints plus the chat web page."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .loader import read_file
from .rag import RagService

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

rag = RagService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    rag.load_folder()
    yield


app = FastAPI(title="DocChat - Document Q&A with Claude", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "documents": len(rag.documents),
        "claude_enabled": bool(config.ANTHROPIC_API_KEY),
        "model": config.CLAUDE_MODEL,
    }


@app.get("/api/documents")
def documents():
    return {"documents": rag.list_documents()}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    name = Path(file.filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in config.SUPPORTED_EXTENSIONS:
        raise HTTPException(400, "Only .txt, .md and .pdf files are supported.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 5 MB.")

    # Save under a sanitized name, then parse it.
    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    target = config.DOCS_DIR / name
    target.write_bytes(data)
    try:
        text = read_file(target).strip()
    except Exception:
        target.unlink(missing_ok=True)
        raise HTTPException(400, "Could not read that file.")
    if not text:
        target.unlink(missing_ok=True)
        raise HTTPException(400, "The file has no readable text.")

    rag.add_document(name, text)
    return {"uploaded": name, "documents": rag.list_documents()}


@app.delete("/api/documents/{name}")
def delete_document(name: str):
    safe_name = Path(name).name
    if not rag.remove_document(safe_name):
        raise HTTPException(404, "Document not found.")
    (config.DOCS_DIR / safe_name).unlink(missing_ok=True)
    return {"documents": rag.list_documents()}


@app.post("/api/ask")
def ask(req: AskRequest):
    if not rag.documents:
        raise HTTPException(400, "Upload at least one document first.")
    return rag.ask(req.question.strip())
