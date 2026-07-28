# CareerOps — Your Local Job Application Pipeline Manager

> A **zero-cloud, privacy-first** career management system that helps you tailor CVs, track applications, and ace interviews.

## ⚡ Quick Start (5 min)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start three terminals:

# Terminal 1: Ollama (LLM for CV tailoring)
ollama serve
ollama pull mistral  # First time only

# Terminal 2: Backend (handles DOCX, API)
python3 backend.py

# Terminal 3: Web server
python3 -m http.server 8000

# 4. Open browser
http://localhost:8000/careerops.html
```

---

## 🎯 What It Does

### 1. Upload Your CV
- **PDF** → Automatic text extraction ✓
- **DOCX** → Automatic text extraction ✓
- **Paste** → Manual copy-paste ✓

### 2. Generate Tailored CVs
Paste a job description → Get a CV tailored to match:
- Keywords from the JD
- Relevant experience reordered
- Cover letter & email draft
- **ATS score** with keyword analysis

⚠️ **NEW:** Red warning if score < 80

### 3. Track Your Applications
Log every job you apply to:
- Company, role, date applied, status
- ATS score, CV version used
- Follow-up dates (red alerts when due)
- Personal notes

### 4. Study from Interviews
Record every interview question:
- Question type (Technical, Behavioral, System Design, etc.)
- Interview round (Phone Screen, Round 1, Round 2, Final)
- Your answer & notes
- **Outcome tracking** (Strong, Okay, Weak, Follow-up)
- Filter by company to prep for next round

---

## 📊 Architecture

```
User Browser (Firefox/Chrome/Safari)
    │
    ├─→ [HTML] careerops.html (1300 lines)
    │   ├─ Tab 1: Deploy (CV generation UI)
    │   ├─ Tab 2: Pipeline (application tracking)
    │   ├─ Tab 3: Runbook (interview questions)
    │   └─ Tab 4: Base Profile (CV management)
    │
    ├─→ [localStorage] Data persistence (100% client-side)
    │   ├─ base-cv (your master CV)
    │   ├─ base-cv-timestamp (version tracking)
    │   ├─ app-log (all applications)
    │   └─ runbook (interview questions)
    │
    └─→ [Fetch API] ↓ HTTP calls
         │
         └─→ Backend: Flask on port 5000
             │
             ├─ POST /api/generate
             │  └─→ Calls Ollama → Returns JSON (CV, cover, email, skills)
             │
             ├─ POST /api/extract-docx (NEW!)
             │  └─→ Parses .docx file → Returns extracted text
             │
             └─ GET /api/health
                └─→ Checks Ollama status
                    │
                    └─→ Ollama (localhost:11434)
                        └─→ LLM inference (Mistral or neural-chat)
```

---

## ✨ Key Features

| Feature | Status | Details |
|---------|--------|---------|
| PDF Upload | ✅ Complete | Drag-drop, text extraction, pdf.js |
| DOCX Upload | ✅ Complete | NEW! python-docx backend extraction |
| CV Tailoring | ✅ Complete | LLM-powered, no fabrication |
| ATS Scoring | ✅ Complete | Keyword matching, 80+ target |
| ATS Warning | ✅ NEW | Red alert if score < 80 |
| PDF Export | ✅ Complete | ATS-safe formatting, professional design |
| Application Tracking | ✅ Complete | Status, follow-ups, version tracking |
| Interview Runbook | ✅ Enhanced | Question types, outcomes, color badges |
| Data Persistence | ✅ Complete | localStorage, browser-local storage |
| Responsive UI | ✅ Complete | Desktop, tablet, mobile friendly |

---

## 📁 Project Structure

```
careerops/
├── careerops.html              # Main app (open in browser)
├── backend.py                  # Flask server (DOCX extraction, Ollama API)
├── requirements.txt            # Python dependencies
│
├── SETUP.md                    # Installation guide (detailed)
├── FEATURES.md                 # Feature status & roadmap
├── QUICK_REFERENCE.md          # UI guide & pro tips
├── IMPLEMENTATION_SUMMARY.md   # What was built & technical details
├── README.md                   # This file
│
└── venv/                       # Python virtual environment
    └── lib/python3.x/site-packages/
        ├── flask
        ├── flask_cors
        ├── python-docx        # ← NEW: DOCX support
        └── ...
```

---

## 🔧 Technology Stack

### Frontend
- **HTML5 + CSS3 + Vanilla JavaScript** (no frameworks)
- **localStorage API** — Client-side persistence
- **Fetch API** — Backend communication
- **jsPDF** — PDF generation (professional CV export)
- **pdf.js** — PDF text extraction

### Backend
- **Flask** — Lightweight Python web server
- **Flask-CORS** — Cross-origin requests
- **python-docx** — DOCX file parsing ✨ NEW!
- **requests** — Ollama API calls

### LLM
- **Ollama** — Local LLM inference
- **Mistral** — Default model (7B params, fast)
- **neural-chat** — Faster alternative (3.5B params)

### Data Storage
- **localStorage** — 100% client-side (5-10MB limit)
- **JSON structure** — Human-readable, easy to export

---

## 📋 What's New (This Build)

### ✨ New Features Added
1. **DOCX Upload Support** — Upload Word docs directly
   - Backend: `/api/extract-docx` endpoint
   - Frontend: `extractDocxText()` function
   - Dependency: `python-docx` library

2. **ATS Warning Alert** — Red alert when score < 80
   - Visual warning box below ATS score
   - Explains risks and next steps
   - Auto-dismisses if score improves

3. **Enhanced Runbook** — Better interview question tracking
   - Question type (Technical, Behavioral, System Design, Leadership, Other)
   - Interview round (Phone Screen, Round 1, Round 2, Final)
   - Outcome tracking (Strong, Okay, Weak, Follow-up)
   - Color-coded badges (type + outcome)

4. **CV Version Tracking** — Know which base profile was used
   - Timestamp saved when profile updated
   - Stored with each application
   - Helps track profile evolution

5. **Better UI/UX** — More informative, less surprises
   - Error messages for failed uploads
   - Field hints and tooltips
   - Loading states with spinners

---

## 🚀 Installation

### Prerequisites
- **Python 3.8+**
- **Ollama** (for AI tailoring) — [Download](https://ollama.ai)
- **Modern browser** (Chrome 90+, Safari 14+, Firefox 88+, Edge 90+)

### Step 1: Clone & Setup
```bash
cd /Users/navinkumar/workrepos/pers-prj/careerops

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start Services (3 terminals)

**Terminal 1: Ollama**
```bash
ollama serve

# First time only:
ollama pull mistral
```

**Terminal 2: Backend**
```bash
cd /Users/navinkumar/workrepos/pers-prj/careerops
source venv/bin/activate
python3 backend.py

# Expected output:
# 🚀 Backend running on http://localhost:5000
# ✓ Health check: http://localhost:5000/api/health
```

**Terminal 3: Web Server**
```bash
cd /Users/navinkumar/workrepos/pers-prj/careerops
python3 -m http.server 8000

# Expected output:
# Serving HTTP on 0.0.0.0 port 8000
```

### Step 3: Open Browser
```
http://localhost:8000/careerops.html
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **SETUP.md** | Installation, troubleshooting, detailed guide |
| **FEATURES.md** | What's implemented, roadmap, testing checklist |
| **QUICK_REFERENCE.md** | UI guide, shortcuts, pro tips, workflows |
| **IMPLEMENTATION_SUMMARY.md** | Technical details, what was built, file structure |
| **README.md** | This file (overview) |

---

## 💡 Usage Examples

### Example 1: Generate Tailored CV
```
1. Tab 4 → Upload your CV (PDF/DOCX/paste)
2. Save base profile
3. Tab 1 → Paste job description from LinkedIn
4. Click "Generate application package"
5. Wait 30-60 sec (LLM processing)
6. See ATS score:
   - ✅ 80+? Download and apply confidently
   - 🟠 60-79? Review missing keywords
   - ❌ <80? ⚠️ See warning, consider editing
7. Download PDF → Apply
8. Click "Log this application →"
```

### Example 2: Track Applications
```
1. Tab 2 → View pipeline (auto-populated after logging)
2. Click "Applied" status → Change to "Screening"
3. Add follow-up date (e.g., 2024-01-22)
4. Add note: "Good fit, mentioned 10 years experience"
5. Auto-saves when you blur the field
6. Stats update automatically
```

### Example 3: Prep for Interview Round 2
```
1. Tab 3 → Filter by company name
2. See all questions from Round 1:
   - "Tell me about a conflict" [Behavioral] [Strong]
   - "Design a URL shortener" [System Design] [Okay]
3. Review answers and notes
4. Spot patterns (they like system design questions)
5. Practice similar questions before Round 2
```

---

## ⚙️ Configuration

### Environment Variables
```bash
# Optional: Set before running backend.py
export OLLAMA_BASE=http://localhost:11434  # Ollama server URL
export OLLAMA_MODEL=mistral                # LLM model to use

python3 backend.py
```

### Switch to Faster Model
```bash
# Pull neural-chat (3.5B, faster than mistral)
ollama pull neural-chat

# Use it:
export OLLAMA_MODEL=neural-chat
python3 backend.py
```

### Port Configuration
- **Frontend:** http://localhost:8000 (configurable via `python3 -m http.server PORT`)
- **Backend:** http://localhost:5000 (hardcoded in backend.py)
- **Ollama:** http://localhost:11434 (configurable via `OLLAMA_BASE` env var)

---

## 🧪 Testing

### Health Check
```bash
# Check if everything is running:
curl http://localhost:5000/api/health

# Expected response:
# {"status": "ok", "ollama": "connected", "model": "mistral", "docx_support": true}
```

### Test DOCX Extraction
```javascript
// In browser console (F12):
const formData = new FormData();
formData.append('file', fileInput.files[0]); // Your DOCX file

fetch('http://localhost:5000/api/extract-docx', {
  method: 'POST',
  body: formData
})
.then(r => r.json())
.then(console.log);
```

### Test Data Persistence
```javascript
// In browser console:
console.log(JSON.parse(localStorage.getItem('app-log')));
console.log(JSON.parse(localStorage.getItem('runbook')));
```

---

## 🐛 Troubleshooting

### "Ollama not running"
```bash
# In Terminal 1:
ollama serve

# First time only:
ollama pull mistral
```

### "Cannot reach backend"
```bash
# Check if port 5000 is in use:
lsof -i :5000

# Make sure backend is running:
cd /Users/navinkumar/workrepos/pers-prj/careerops
source venv/bin/activate
python3 backend.py
```

### "DOCX upload fails"
Try these in order:
1. Re-save the DOCX in Word/Google Docs
2. Copy text manually and paste
3. Export DOCX as PDF, upload PDF instead

### "Data not saving"
- Disable private/incognito browsing
- Clear browser cache
- Try a different browser
- Check localStorage isn't full: `localStorage.setItem('test', 'data')`

---

## 📊 Data Schema

### Applications (localStorage: `app-log`)
```json
{
  "id": "unique-id",
  "company": "Acme Corp",
  "role": "Senior Engineer",
  "jd": "full job description text",
  "dateApplied": "2024-01-15",
  "status": "Applied|Screening|Interview|Offer|Rejected|Ghosted",
  "followUpDate": "2024-01-22",
  "notes": "Good culture fit",
  "tailoredCV": "markdown CV text",
  "coverLetter": "cover letter text",
  "emailDraft": "email draft text",
  "skills": ["Kubernetes", "Terraform", "AWS"],
  "atsScore": 85,
  "baseCvVersion": "2024-01-15T10:30:00Z"
}
```

### Interview Questions (localStorage: `runbook`)
```json
{
  "Acme Corp — Senior Engineer": [
    {
      "id": "unique-id",
      "question": "How do you handle production outages?",
      "type": "behavioral|technical|systemdesign|leadership|other",
      "round": "Phone Screen|Round 1|Round 2|Final",
      "outcome": "strong|okay|weak|follow-up",
      "notes": "Focused on communication and RCA",
      "date": "2024-01-18"
    }
  ]
}
```

---

## 🗺️ Roadmap (Phase 2)

- [ ] CSV/JSON export of applications and questions
- [ ] Analytics dashboard (success rate, time-to-offer, trends)
- [ ] Bulk actions (mark multiple as rejected)
- [ ] Email templates with auto-fill
- [ ] Interview prep checklist (links to runbook)
- [ ] Question statistics (common patterns, outcomes)
- [ ] Optional cloud backup (encrypted)

---

## 🔒 Privacy & Data

- ✅ **100% Local** — All data in browser's localStorage
- ✅ **No Cloud** — Nothing sent to external servers (except Ollama API calls)
- ✅ **No Tracking** — No analytics, no cookies
- ✅ **Exportable** — Can backup/import JSON anytime
- ✅ **Deletable** — `localStorage.clear()` in console to wipe everything

---

## ⚡ Performance

### First Run
- Backend startup: ~2s
- Ollama model load: 5-10s (first time only)
- First CV generation: 30-60s

### Subsequent Runs
- CV generation: 15-30s
- ATS scoring: <1s
- PDF export: <2s
- UI renders: <100ms

### Memory
- Browser: ~50MB (grows with large application logs)
- Backend: ~100MB
- Ollama: 1-2GB (depends on model size)

---

## 🤝 Contributing

This is a personal project. To add features:
1. Edit `careerops.html` (frontend)
2. Edit `backend.py` (backend)
3. Test locally
4. Keep data models backwards-compatible

---

## ✅ Quick Checklist: First Time

- [ ] Read SETUP.md
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Start Ollama: `ollama serve`
- [ ] Start backend: `python3 backend.py`
- [ ] Start web server: `python3 -m http.server 8000`
- [ ] Open: `http://localhost:8000/careerops.html`
- [ ] Tab 4: Upload/paste CV
- [ ] Tab 1: Paste JD, generate CV
- [ ] Tab 2: Log application
- [ ] Tab 3: Add interview question
- [ ] Refresh: Data persists ✓

---

## 📞 Support

### Debug
```javascript
// In browser console (F12):
console.log(localStorage);
fetch('http://localhost:5000/api/health').then(r=>r.json()).then(console.log);
```

### Export Data (Backup)
```javascript
copy(JSON.stringify({
  applications: JSON.parse(localStorage.getItem('app-log')),
  runbook: JSON.parse(localStorage.getItem('runbook')),
  baseCv: localStorage.getItem('base-cv')
}, null, 2))
// Paste into .json file
```

### Clear Data (Fresh Start)
```javascript
localStorage.clear();
location.reload();
```

---

## 📜 License

Personal project. Use as-is.

---

## 🎉 Happy Job Hunting!

**Start here:**
1. Read [SETUP.md](SETUP.md) for installation
2. Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for UI guide
3. Check [FEATURES.md](FEATURES.md) for what's implemented

**Have questions?** Check console (F12) for error messages, or review the docs above.

---

*Last updated: 2024-01-28*  
*Built with: Flask + Ollama + Vanilla JS + localStorage*
