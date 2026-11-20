# DocChat: Document Q&A with RAG and the Claude API

DocChat lets you upload documents (.txt, .md, .pdf) and ask questions in plain language. It finds the most relevant passages, sends only those to Claude, and returns a short answer with the sources it used.

Built with **Python, FastAPI, scikit-learn (TF-IDF retrieval), pypdf and the Anthropic Claude API**, with a simple web chat page.

## Features

- Upload `.txt`, `.md` and `.pdf` files, or drop files in `sample_docs/`
- Retrieval-Augmented Generation (RAG): chunking with overlap, TF-IDF search, cosine similarity
- Answers grounded in your documents, with citations such as `[leave_policy.txt #1]`
- Says "I could not find that" instead of guessing when the documents have no answer
- Works **without an API key** in retrieval-only mode (shows the two best matching passages), so you can demo it anywhere
- REST API with input validation, upload size limit, and safe file names
- Automated tests with pytest (no API key needed)

## How it works

```
Question
   |
   v
TF-IDF search over chunks  -->  top 4 chunks (with scores)
                                     |
                                     v
              Claude reads only those chunks and writes a cited answer
```

1. `loader.py` reads files into text.
2. `chunker.py` splits text into 120-word chunks with a 30-word overlap.
3. `retriever.py` builds a TF-IDF index (unigrams and bigrams) and ranks chunks by cosine similarity.
4. `llm.py` sends the question and the top chunks to Claude with a prompt that forbids outside knowledge.
5. `rag.py` ties these together and falls back to retrieval-only mode if there is no key or the API call fails.
6. `main.py` exposes the FastAPI endpoints and serves the web page.

## Setup

Requires Python 3.10 or newer.

```bash
cd docchat
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Add your Claude API key (optional but recommended)

Get a key from the Anthropic Console, then set it in your terminal:

```bash
export ANTHROPIC_API_KEY="your_key_here"      # Windows PowerShell: $env:ANTHROPIC_API_KEY="your_key_here"
```

Never commit your key to GitHub. `.env` is already in `.gitignore`.

### Run

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and try:

- "How many days of annual leave do employees get?"
- "Can I work from another country?"
- "Why do RAG systems use overlapping chunks?"

### Run the tests

```bash
pytest
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Status, document count, whether Claude is enabled |
| GET | `/api/documents` | List indexed documents |
| POST | `/api/upload` | Upload a file (multipart, field name `file`) |
| DELETE | `/api/documents/{name}` | Remove a document |
| POST | `/api/ask` | Body `{"question": "..."}`, returns answer, mode and sources |

Interactive docs are available at http://127.0.0.1:8000/docs.

## Settings

Set as environment variables: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` (default `claude-sonnet-5-5`), `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `MIN_SCORE`, `DOCS_DIR`.

## Project structure

```
docchat/
  app/
    main.py        FastAPI routes
    rag.py         RAG pipeline and fallback logic
    loader.py      Read txt/md/pdf
    chunker.py     Overlapping chunks
    retriever.py   TF-IDF + cosine similarity
    llm.py         Claude API call and prompt
    config.py      Settings
    static/        Web page (HTML, CSS, JS)
  sample_docs/     Three demo documents
  tests/           pytest tests
```




**DocChat: Document Q&A chatbot (RAG)** | Python, FastAPI, scikit-learn, Claude API, JavaScript

- Built a Retrieval-Augmented Generation app that answers questions over uploaded PDF, Markdown and text files, returning cited answers grounded only in the documents.
- Implemented overlapping word-based chunking and TF-IDF retrieval with cosine similarity; sent the top 4 passages to the Claude API with a prompt that refuses to answer outside the sources.
- Designed a REST API (upload, ask, list, delete) with input validation, file-size limits and a retrieval-only fallback when the LLM is unavailable; covered it with 17 pytest tests.
