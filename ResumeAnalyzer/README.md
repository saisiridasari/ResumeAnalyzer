# ResumeIQ — AI-Powered Resume Analyzer

A production-ready full-stack web application that uses NLP and machine learning to analyze resumes against job descriptions and generate actionable improvement suggestions.

---

## Features

- **Resume Parsing** — Extracts name, email, phone, skills, education, experience, certifications, and projects from PDF and DOCX files using spaCy NER and regex
- **Skill Extraction** — Cross-references 200+ tech and professional skills; normalizes aliases (e.g. `ReactJS` → `react`)
- **Job Description Matching** — TF-IDF vectorization and cosine similarity measure keyword overlap; rule-based logic evaluates education and experience levels
- **Weighted Scoring** — Produces a 1–100 match score: Skills 50%, Experience 20%, Education 15%, Certifications 10%, Keywords 5%
- **ATS Score Estimate** — Estimates Applicant Tracking System compatibility
- **Actionable Suggestions** — Skill gaps, certification recommendations, keyword insertions, ATS tips, project guidance
- **Downloadable Report** — Plain-text analysis report download
- **Responsive UI** — Dark-themed professional dashboard with animated score ring, skill tags, breakdown bars

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.10+, Flask 3.0, Flask-CORS |
| NLP | spaCy (`en_core_web_sm`), NLTK |
| ML | scikit-learn (TF-IDF, cosine similarity) |
| Document Parsing | pdfplumber, PyPDF2, python-docx |
| Frontend | Vanilla HTML5/CSS3/JavaScript (ES2020) |
| Fonts | DM Serif Display + DM Sans (Google Fonts) |

---

## Project Structure

```
ResumeAnalyzer/
├── app.py                  # Flask application, API routes
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore
├── README.md
│
├── uploads/                # Uploaded resume files (auto-created)
│
├── services/
│   ├── parser.py           # PDF/DOCX parsing + NER entity extraction
│   ├── extractor.py        # Skill extraction from text (200+ skills)
│   ├── matcher.py          # Resume vs JD matching (TF-IDF + cosine)
│   ├── scorer.py           # Weighted score calculation
│   └── suggestions.py      # Actionable improvement suggestions
│
├── models/                 # Reserved for ML model artifacts
│
├── static/
│   ├── css/
│   │   ├── main.css        # Core styles + upload page
│   │   └── results.css     # Dashboard / results page styles
│   └── js/
│       ├── main.js         # Upload form logic + API calls
│       └── results.js      # Dashboard rendering
│
└── templates/
    ├── index.html          # Upload + JD form page
    └── results.html        # Analysis dashboard
```

---

## Setup & Installation

### Prerequisites
- Python 3.10 or later
- pip

### 1. Clone or unzip the project
```bash
cd ResumeAnalyzer
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download spaCy language model
```bash
python -m spacy download en_core_web_sm
```

### 5. Download NLTK data
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger'); nltk.download('punkt_tab')"
```

### 6. Configure environment
```bash
cp .env.example .env
# Edit .env if needed (defaults work for local development)
```

### 7. Run the application
```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## API Reference

### `POST /api/upload`
Upload a resume file.

**Request:** `multipart/form-data` with field `resume` (PDF or DOCX, max 16 MB)

**Response:**
```json
{
  "success": true,
  "filename": "uuid_original.pdf",
  "original_name": "original.pdf"
}
```

---

### `POST /api/parse`
Parse an uploaded resume.

**Request:**
```json
{ "filename": "uuid_original.pdf" }
```

**Response:** Extracted resume fields (name, email, phone, skills, education, etc.)

---

### `POST /api/analyze`
Full analysis: parse + extract + match + score + suggestions.

**Request:**
```json
{
  "filename": "uuid_original.pdf",
  "job_description": "We are looking for a Senior Python Developer..."
}
```

**Response:**
```json
{
  "success": true,
  "candidate": { "name": "...", "email": "...", "phone": "..." },
  "parsed_resume": { ... },
  "resume_skills": [...],
  "jd_skills": [...],
  "match_result": {
    "skill_match": { "matched": [...], "missing": [...], "score": 72.5 },
    "experience_match": { "resume_years": 3, "required_years": 2, "score": 100 },
    "education_match": { ... },
    "certification_match": { ... },
    "keyword_match": { "matched_keywords": [...], "missing_keywords": [...] }
  },
  "scores": {
    "overall": 68.4,
    "rating": "Good Match",
    "breakdown": { ... },
    "ats_score": 71.2,
    "percentile": 58
  },
  "suggestions": { ... }
}
```

---

### `GET /api/health`
Health check.

---

## Deployment

### Using Gunicorn (production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables for Production
```
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<strong-random-key>
MAX_CONTENT_LENGTH=16777216
```

### Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t resumeiq .
docker run -p 5000:5000 resumeiq
```

### Heroku
```bash
heroku create your-resumeiq-app
git push heroku main
heroku run python -m spacy download en_core_web_sm
```

---

## Scoring Model

| Category | Weight | Method |
|---|---|---|
| Skills | 50% | Set intersection (resume skills ∩ JD skills) + partial match |
| Experience | 20% | Year detection regex vs JD required years |
| Education | 15% | Degree level mapping (PhD > Master > Bachelor > Associate) |
| Certifications | 10% | Keyword matching against 30+ certification patterns |
| Keywords | 5% | TF-IDF + cosine similarity on full text |

**Overall Score = Σ(category_score × weight)**

---

## Notes

- The `uploads/` directory stores files temporarily. For production, consider using S3 or equivalent cloud storage and adding a cleanup job.
- spaCy NER is used for name extraction; the first PERSON entity in the top 500 characters is used as the candidate name.
- All analysis results are stored in `sessionStorage` on the frontend and passed to the results page without a separate API call.

---

## License

MIT License — free to use, modify, and distribute.
