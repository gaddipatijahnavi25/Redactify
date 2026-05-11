# AI PII Redactor 🔒

> **Automatically detect and redact Personally Identifiable Information (PII) from CSV, JSON, TXT, PDF, and image files.**

Built for hackathons and privacy-conscious AI/ML workflows.

---

## ✨ Features

| Capability | Details |
|---|---|
| **File types** | TXT · CSV · JSON · PDF · PNG · JPG |
| **PII detected** | Email, Phone (IN/INTL), Aadhaar, PAN, SSN, Passport, Credit Card, IFSC, UPI, IP, MAC, URL, DOB, Vehicle No. |
| **Detection engine** | Regex patterns + spaCy NLP (`en_core_web_sm`) |
| **Image & PDF** | Tesseract OCR → detect → black-bar visual redaction |
| **Output** | Redacted file (base64 download) + structured JSON audit report |
| **UI** | Drag-and-drop dark-mode single-page app |

---

## 🏗️ Architecture

```
Upload → File Type Detection → Pipeline Router
    ├── TEXT/CSV/JSON → Detect PII → Replace with [ENTITY_TYPE]
    └── IMAGE/PDF     → OCR → Detect PII → Black-bar bounding boxes
         ↓
    Report Generator → JSON Response { redacted_file_b64, report }
```

---

## 📁 Project Structure

```
pii/
├── backend/
│   ├── main.py                   # FastAPI entry point
│   ├── requirements.txt
│   ├── api/
│   │   └── redact.py             # POST /api/redact
│   ├── core/
│   │   ├── config.py             # Pydantic settings
│   │   ├── file_handler.py       # Upload/save helpers
│   │   └── file_type.py          # Extension → FileType enum
│   ├── detection/
│   │   ├── detector.py           # Hybrid regex + spaCy detector
│   │   └── patterns.py           # 18 compiled regex patterns
│   ├── redaction/
│   │   ├── text_redactor.py      # Span replacement (end→start)
│   │   └── image_redactor.py     # OpenCV black-bar redaction
│   ├── ocr/
│   │   └── ocr_engine.py         # pytesseract wrapper
│   ├── pipelines/
│   │   ├── text_pipeline.py      # TXT / CSV / JSON
│   │   └── image_pipeline.py     # Image / PDF
│   └── reporting/
│       └── report.py             # JSON audit report
├── frontend/
│   ├── index.html                # SPA with drag-drop upload
│   ├── style.css                 # Dark glassmorphism UI
│   └── app.js                    # Fetch API + result rendering
├── data/
│   ├── uploads/                  # Saved uploads
│   └── outputs/                  # Redacted outputs
├── samples/
│   ├── sample.csv
│   └── sample.json
└── run_backend.sh                # One-command startup
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)** – add to PATH for image/PDF support
- **spaCy model** (optional but recommended for name/org detection):
  ```bash
  python -m spacy download en_core_web_sm
  ```

### Install & Run

```bash
# 1. Install deps
cd backend
pip install -r requirements.txt

# 2. Download spaCy model (optional)
python -m spacy download en_core_web_sm

# 3. Start server
uvicorn main:app --reload --port 8000
```

Open **http://127.0.0.1:8000** — the UI is served automatically.

---

## 🌐 API Reference

### `POST /api/redact`

**Input:** `multipart/form-data` — field `file`

**Output:**
```json
{
  "filename": "customers.csv",
  "file_type": "csv",
  "redacted_file_b64": "<base64>",
  "report": {
    "generated_at": "2025-...",
    "filename": "customers.csv",
    "file_type": "csv",
    "pii_summary": {
      "total_detected": 12,
      "by_category": { "EMAIL": 4, "AADHAAR": 3, "PHONE_IN": 5 },
      "regex_detections": 10,
      "nlp_detections": 2,
      "confidence_estimate": 0.95
    },
    "detections": [
      { "entity_type": "EMAIL", "original_text": "user@example.com", "source": "regex", "score": 1.0 }
    ]
  }
}
```

### `GET /health`

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## ⚙️ Configuration

Create a `.env` file in `backend/`:

```env
UPLOAD_DIR=../data/uploads
OUTPUT_DIR=../data/outputs
MAX_FILE_SIZE_MB=50
OCR_LANGUAGE=eng
```

---

## 🧪 Sample Files

| File | PII types |
|---|---|
| `samples/sample.csv` | Name, Email, Phone, Aadhaar, PAN, DOB |
| `samples/sample.json` | Name, Email, Phone, SSN, Passport, IP, URL |

---

## 📜 License

MIT © 2025
