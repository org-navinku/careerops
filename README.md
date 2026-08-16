# CareerOps — Job Application Pipeline Manager

A **privacy-first** career management system that helps you tailor CVs, track applications, and prep for interviews.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set required env vars
export AWS_REGION=us-east-1
export CAREEROPS_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 3. Start backend
python3 backend.py

# 4. Start web server (separate terminal)
python3 -m http.server 8000

# 5. Open browser
open http://localhost:8000/careerops.html
```

LLM provider (OpenAI, Anthropic, or custom) is configured in the app's Settings tab.

---

## What It Does

### Tab 1: Deploy — Generate Tailored CVs
Paste a job description → get a CV tailored to match:
- Keywords reordered and emphasized
- ATS score with keyword analysis (target 80+)
- **Category-by-category comparison** — approve/reject changes individually
- Cover letter & email draft
- DOCX export

### Tab 2: Pipeline — Track Applications
- Company, role, date, status tracking
- ATS score and CV version per application
- Follow-up date alerts
- Email subject/to fields

### Tab 3: Runbook — Interview Questions
- Question type (Technical, Behavioral, System Design, etc.)
- Round tracking (Phone Screen → Final)
- Outcome tracking (Strong, Okay, Weak)
- Filter by company to prep for next round

### Tab 4: Base Profile — CV Management
- Upload PDF/DOCX or paste text
- Stored in S3 with version tracking
- Every tailored CV is generated from this

---

## Architecture

```
Browser (careerops.html)
    │
    ├─→ localStorage (base CV, settings)
    │
    └─→ Flask Backend (port 5001)
         ├─ POST /api/generate        → LLM API (OpenAI/Anthropic/Custom)
         ├─ POST /api/compare-cv      → CV parsing + category comparison
         ├─ POST /api/assemble-cv     → Merge approved changes
         ├─ POST /api/generate-docx   → Word document generation
         ├─ POST /api/extract-docx    → DOCX text extraction
         ├─ /api/applications         → DynamoDB CRUD
         ├─ /api/runbook              → DynamoDB CRUD
         └─ /api/health               → Status check
```

---

## Project Structure

```
careerops/
├── careerops.html          # Frontend (single-page app)
├── backend.py              # Flask backend (all API logic)
├── requirements.txt        # Python dependencies
├── conftest.py             # pytest root config (mocks boto3)
├── tests/                  # pytest + Hypothesis test suite
├── Dockerfile              # Container build
├── docker-compose.yml      # Local multi-service setup
├── deploy-dynamodb.sh      # DynamoDB table creation script
├── scripts/push-to-ecr.sh  # ECR deployment script
├── .github/workflows/      # GitHub Actions CI
├── .gitlab-ci.yml          # GitLab CI config
├── SETUP.md                # Detailed installation guide
├── FEATURES.md             # Feature status & roadmap
├── QUICK_REFERENCE.md      # UI workflow guide
├── DOCKER_DEPLOYMENT.md    # Container deployment guide
└── RECORDING_FEATURE.md    # Interview recording feature docs
```

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | HTML5, Vanilla JS, CSS3, jsPDF, pdf.js |
| Backend | Flask, Flask-CORS, python-docx, boto3, cryptography |
| LLM | OpenAI, Anthropic, or any OpenAI-compatible API |
| Storage | AWS DynamoDB (apps, runbook), S3 (CV files), localStorage |
| Testing | pytest, Hypothesis (134 tests, property-based) |
| Deploy | Docker, ECR, GitHub Actions, GitLab CI |

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_REGION` | Yes | AWS region for DynamoDB/S3 |
| `CAREEROPS_ENCRYPTION_KEY` | Yes | Fernet key for encrypting API keys at rest |
| `CAREEROPS_USERNAME` | No | Login username (if auth enabled) |
| `CAREEROPS_PASSWORD` | No | Login password (if auth enabled) |
| `OPENAI_API_KEY` | No | Fallback OpenAI key (prefer in-app Settings) |
| `FLASK_PORT` | No | Backend port (default: 5001) |
| `FLASK_HOST` | No | Backend host (default: 127.0.0.1) |

LLM providers are configured in the app UI under Settings (keys encrypted at rest in DynamoDB).

---

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -q

# Run with verbose output
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_cv_comparison_api.py -v
```

134 tests covering:
- CV parsing (property-based + unit)
- Comparison engine (property-based + unit)
- Final assembler (property-based + unit)
- Score computation (property-based)
- API endpoints (integration)
- Frontend logic (property-based)
- Email fields, CV upload/download/delete

---

## Docker

```bash
# Build and run locally
docker-compose up --build

# Push to ECR
./scripts/push-to-ecr.sh
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for full deployment guide.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [SETUP.md](SETUP.md) | Detailed installation & troubleshooting |
| [FEATURES.md](FEATURES.md) | Feature status & roadmap |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | UI workflows & tips |
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Container deployment |
| [RECORDING_FEATURE.md](RECORDING_FEATURE.md) | Interview recording feature |
