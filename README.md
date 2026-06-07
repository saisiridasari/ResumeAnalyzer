# ResumeIQ

A Flask web application that analyzes a resume against a job description and returns a match score, an ATS-compatibility estimate, and concrete suggestions for improvement. Matching is done with classical NLP and rule-based logic — spaCy for entity extraction, a curated skill dictionary, and a weighted scoring model. No large language model and no database.

## Features

- Upload a resume (PDF or DOCX) and paste a target job description.
- Extract structured fields from the resume: name, contact details, skills, education, experience, and certifications.
- Score the match across five weighted categories: skills (50%), experience (20%), education (15%), certifications (10%), and keywords (5%).
- Report an overall match score (0–100), an ATS-compatibility estimate, and a percentile band.
- Generate actionable suggestions: missing skills, recommended certifications, keywords to add, ATS formatting tips, and a prioritized action plan.
- Download a plain-text report of the results.

## Tech Stack

- **Backend:** Python, Flask 3, Werkzeug, Flask-CORS
- **NLP and analysis:** spaCy (`en_core_web_sm`), scikit-learn, NLTK
- **File parsing:** pdfplumber and PyPDF2 (PDF), python-docx (DOCX)
- **Frontend:** vanilla HTML5, CSS3, and JavaScript — no framework, no build step
- **Production server:** gunicorn

There is no database. Uploaded files are stored on disk, and analysis results are held in the browser for the duration of the session.

## Project Structure

```
.
├── app.py              # Flask app: routes and pipeline orchestration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── services/           # Analysis logic
│   ├── parser.py       # PDF/DOCX -> text -> structured fields
│   ├── extractor.py    # Skill detection (dictionary + spaCy)
│   ├── matcher.py      # Resume vs. job description comparison
│   ├── scorer.py       # Weighted score, ATS estimate, percentile
│   └── suggestions.py  # Suggestions, strengths, action plan
├── static/             # CSS and JavaScript
└── templates/          # index.html (upload) and results.html
```

## Getting Started

### Prerequisites

- Python 3.11 or newer

### Installation

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd ResumeAnalyzer

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Configure environment variables
cp .env.example .env            # edit values as needed
```

### Run (development)

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

### Run (production)

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

## How It Works

1. The browser uploads the resume to `/api/upload`, which validates the file type and stores it.
2. It then calls `/api/analyze` with the saved filename and the job description.
3. The server runs a pipeline: parse the resume, extract skills from both texts, match across the five categories, compute the scores, and generate suggestions.
4. The result is returned as JSON and rendered in the results dashboard.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Upload page |
| `/results` | GET | Results dashboard |
| `/api/upload` | POST | Validate and store the resume; returns the saved filename |
| `/api/analyze` | POST | Run the full analysis and return JSON |
| `/api/parse` | POST | Parse a resume only (standalone/debug endpoint) |
| `/api/health` | GET | Health check |

## Notes and Limitations

- Only text-based PDF and DOCX files are supported. Scanned, image-only PDFs are not processed, since the app reads the embedded text layer and does not perform OCR.
- Skills are detected against a curated dictionary, so terms outside that vocabulary will not be matched.
- The ATS score and percentile are heuristic estimates, not the output of a real ATS engine.
- Uploaded files are not removed automatically, and results are stored per browser tab, so there is no history or user account system.
