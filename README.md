# 📄 Enterprise Document Intelligence System

A production-ready AI system that extracts structured data from documents (PDFs/images) using OCR, Rule-based extraction, LLM validation, and confidence scoring.

## 🎯 Features

- **OCR Engine**: Extract text from multi-page PDFs
- **Rule-Based Extraction**: Fast, deterministic field extraction using regex
- **LLM Integration**: AI-powered extraction using OpenAI for complex/unstructured data
- **Validation & Cleaning**: Automatic data normalization and type conversion
- **Confidence Scoring**: Reliability scores for each extracted field
- **FastAPI Backend**: Production-ready REST API
- **Streamlit UI**: User-friendly web interface

## 🏗️ Architecture

```
Upload Document
    ↓
OCR (Extract Text)
    ↓
Rule-Based Extraction
    ↓
LLM Extraction (Optional)
    ↓
Merge Results
    ↓
Validation & Type Conversion
    ↓
Confidence Scoring
    ↓
JSON Output
```

## 📦 Tech Stack

- **Python 3.8+**
- **FastAPI**: REST API framework
- **Streamlit**: Web UI
- **PaddleOCR**: PDF/image text extraction (completely free, runs locally)
- **Google Gemini API**: LLM (free tier available)
- **Pydantic**: Data validation
- **Regex**: Pattern matching

## 🚀 Quick Start

### 1. Setup

Clone the repository:
```bash
cd ai-document-intelligence/enterprise-document-intelligence-system
```

Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (get free key from https://ai.google.dev)
```

### 2. Run Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Open browser: http://localhost:8501

### 3. Run FastAPI Backend

```bash
python -m uvicorn app.api.main:app --reload
```

API Docs: http://localhost:8000/docs

### 4. Run Tests

```bash
pytest tests/
```

## 📋 Supported Document Types

- **Invoice**: Extract invoice number, date, vendor, amount, due date
- **Bill**: Extract bill details and service information
- **Receipt**: Extract transaction details and items
- **Job Description**: Extract job title, requirements, salary

## 🔗 API Endpoints

### Extract Single Document
```bash
POST /extract
Content-Type: multipart/form-data

file: [PDF file]
document_type: "invoice" (optional)
```

Response:
```json
{
  "success": true,
  "data": {
    "document_name": "invoice.pdf",
    "extracted_fields": {
      "invoice_number": {
        "value": "INV-2024-001",
        "confidence": 0.95,
        "source": "rule"
      }
    },
    "overall_confidence": 0.92,
    "page_count": 1,
    "processing_time": 2.5
  }
}
```

### Extract Batch
```bash
POST /extract-batch
Content-Type: multipart/form-data

files: [PDF files...]
```

### Health Check
```bash
GET /health
```

### Document Types
```bash
GET /document-types
```

## 📁 Project Structure

```
app/
├── src/
│   ├── ocr.py              # OCR engine (PDF text extraction)
│   ├── rule_extractor.py   # Rule-based extraction
│   ├── llm_extractor.py    # LLM extraction
│   ├── validation.py       # Data validation & cleaning
│   └── pipeline.py         # Main processing pipeline
├── api/
│   └── main.py             # FastAPI application
├── models/
│   └── schemas.py          # Pydantic models
├── config/                 # Configuration files
├── input/                  # Sample documents
└── db/                     # Database (future)

ui/
└── streamlit_app.py        # Streamlit web UI

tests/
├── test_ocr.py
├── test_rule_extractor.py
├── test_validation.py
└── test_pipeline.py

requirements.txt            # Python dependencies
.env.example               # Environment variables template
```

## 🧪 Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_ocr.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📈 Development Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] OCR engine
- [x] Rule-based extraction
- [x] Data validation
- [x] Confidence scoring
- [x] Streamlit UI

### Phase 2: AI Integration
- [ ] LLM extraction (in progress)
- [ ] Hybrid results merging
- [ ] JSON parsing

### Phase 3: Backend API ✅
- [x] FastAPI setup
- [x] File upload handling
- [x] Batch processing

### Phase 4: Advanced Features
- [ ] RAG system (vector database)
- [ ] Evaluation metrics
- [ ] Logging system
- [ ] Data redaction (PII masking)
- [ ] Performance optimization

## 🔐 Security

- File upload validation
- API rate limiting (coming soon)
- PII redaction (coming soon)
- Error handling without exposing sensitive data

## 📝 Example Usage

### Python Script
```python
from app.src.pipeline import ExtractionPipeline

pipeline = ExtractionPipeline()
result = pipeline.process_document("invoice.pdf", "invoice")

print(f"Confidence: {result.overall_confidence:.0%}")
for field_name, field in result.extracted_fields.items():
    print(f"{field_name}: {field.value}")
```

### Curl Request
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@invoice.pdf" \
  -F "document_type=invoice"
```

## 🐛 Troubleshooting

### ModuleNotFoundError: No module named 'app'
Run from project root directory:
```bash
cd enterprise-document-intelligence-system
python -m app.src.pipeline
```

### OPENAI_API_KEY not found
Create `.env` file with your API key:
```bash
OPENAI_API_KEY=sk-...
```

### PDF extraction not working
Ensure PDF is not corrupted and contains readable text (not scanned images)

## 📚 Documentation

- [API Docs](http://localhost:8000/docs) - Interactive API documentation
- [Data Models](app/models/schemas.py) - Pydantic models
- [Rules & Patterns](app/src/rule_extractor.py) - Extraction patterns

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test: `pytest tests/`
3. Commit: `git commit -m "Add new feature"`
4. Push: `git push origin feature/new-feature`
5. Create Pull Request

## 📄 License

MIT License - See LICENSE file

## 👨‍💻 Developer

**Rajan Kant**

## 📞 Support

For issues and feature requests, open an issue on GitHub.

---

**Last Updated**: May 2026
**Status**: Phase 2 (LLM Integration with Free APIs)
**Current Features**: PaddleOCR + Rule-based Extraction + Gemini LLM