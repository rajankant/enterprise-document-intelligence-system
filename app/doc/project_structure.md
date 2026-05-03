# Production Folder Structure

doc_intelligence/
│
├── app/                        # Main application
│   ├── main.py                # FastAPI entry point
│   ├── api/                   # API routes
│   │   └── routes.py
│   ├── core/                  # Config, settings
│   │   └── config.py
│   ├── models/                # Pydantic schemas
│   │   └── invoice.py
│   ├── services/              # Business logic
│   │   ├── extractor.py
│   │   ├── ocr.py
│   │   ├── llm.py
│   │   ├── rules.py
│   │   ├── validator.py
│   │   └── scorer.py
│   ├── db/                    # DB layer (optional)
│   │   └── database.py
│
├── rag/                       # RAG (later phase)
│   └── vector_store.py
│
├── ui/                        # Streamlit UI
│   └── app.py
│
├── tests/                     # Unit tests
│
├── Dockerfile
├── requirements.txt
└── README.md