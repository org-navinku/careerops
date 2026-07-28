# CareerOps Setup Guide

## What is CareerOps?

CareerOps is a local-first career management system that helps you:
1. **Upload your CV** (PDF or DOCX) and maintain a base profile
2. **Generate tailored CVs** optimized for each job description
3. **Track all applications** with ATS scores, status, and follow-up dates
4. **Log interview questions** with outcomes and question types
5. **Export your data** for analysis

---

## Prerequisites

### Option A: With Ollama (Full AI-powered tailoring)
- **Ollama** (for local LLM inference) — [install from ollama.ai](https://ollama.ai)
- **Python 3.8+**
- **Modern browser** (Chrome, Safari, Firefox, Edge)

### Option B: Without Ollama (Manual tailoring only)
- Just **Python 3.8+** and a **modern browser**
- You can still upload CVs, track applications, and log interview questions
- CV generation will fail until Ollama is running

---

## Installation (5 minutes)

### 1. Navigate to the project
```bash
cd /Users/navinkumar/workrepos/pers-prj/careerops
```

### 2. Set up the virtual environment (first time only)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start Ollama (if you want AI tailoring)
```bash
# In a separate terminal:
ollama serve

# On first run, pull the model:
ollama pull mistral
```

### 4. Start the backend
```bash
# Terminal 2:
source venv/bin/activate
python3 backend.py
```

### 5. Start the web server
```bash
# Terminal 3:
cd /Users/navinkumar/workrepos/pers-prj/careerops
python3 -m http.server 8000
```

### 6. Open your browser
```
http://localhost:8000/careerops.html
```

---

## Quick Tour

### **Tab 1: Deploy** — Generate tailored applications
- Paste a job description
- CV is automatically tailored to match keywords and requirements
- ATS score calculated (target: 80+)
- Download PDF and cover letter
- Log the application to your pipeline

### **Tab 2: Pipeline** — Track all applications
- See status of every company/role you've applied to
- ATS score for each application
- Track follow-up dates (red highlights when due)
- Notes field for each application
- Inline editing (everything auto-saves)

### **Tab 3: Runbook** — Learn from interviews
- Log every interview question you're asked
- Track question type (technical, behavioral, system design, leadership, other)
- Record which interview round (phone screen, round 1, final)
- Add your answer and how you'd improve
- Track feedback/outcome (strong, okay, weak, follow-up)
- Filter by company/role to prep for next round

### **Tab 4: Base Profile** — Manage your master CV
- **Upload PDF or DOCX** — text extracted automatically
- Or paste your CV directly
- Save changes (stored locally in browser)
- This is your source of truth — edits don't affect past applications

---

## Features in Detail

### ✅ **CV Upload (PDF or DOCX)**
- Drag-and-drop or click to browse
- Automatic text extraction
- Review extracted text before saving
- Fallback: paste manually if upload fails

### ✅ **ATS Scoring**
- Automatic score on CV generation (target: 80+)
- Keyword matching analysis
- Shows matched vs. missing keywords
- Warning alert if score < 80
- "Rescore edits" button if you manually edit the CV

### ✅ **Application Tracking**
- Log company, role, date applied, status, follow-up date
- Stores tailored CV, cover letter, email draft
- ATS score recorded for each application
- Base CV version tracked (so you know which profile version was used)
- Stats dashboard: total, active, in-interview, follow-ups due

### ✅ **Interview Runbook**
- Questions tagged by type (technical, behavioral, system design, leadership)
- Round tracking (phone screen, round 1, round 2, final)
- Your answer and notes field
- Outcome tracking (strong, okay, weak, follow-up)
- Filter and browse by company/role

### ✅ **Data Persistence**
- All data stored in browser's **localStorage** (survives browser restart)
- Can export/backup JSON if needed
- No cloud sync (completely private, on your machine)

---

## Troubleshooting

### "Ollama not running"
**Solution:** Start Ollama in a separate terminal:
```bash
ollama serve
```
First time only, pull the model:
```bash
ollama pull mistral
```

### "Cannot reach backend" error
**Solution:** Make sure backend is running:
```bash
source venv/bin/activate
python3 backend.py
```
Should show: `🚀 Backend running on http://localhost:5000`

### PDF upload fails
**Reason:** The PDF may be scanned images only (no text layer)
**Solution:** Copy and paste the CV text manually

### DOCX upload fails
**Reason:** The DOCX may be corrupted or use unsupported formats
**Solution:** Re-save the DOCX in Word/Google Docs, or paste the text manually

### Data not saving
**Reason:** Browser localStorage may be full or disabled
**Solution:**
- Check if private browsing is enabled (disable it)
- Clear browser cache and try again
- Use a different browser

### CV generation slow
**Reason:** LLM is processing (can take 30-60 seconds)
**Solution:** Be patient, it's thinking. First run of a model may be slower.

---

## Data Format (What Gets Stored)

### Applications (localStorage key: `app-log`)
```json
[
  {
    "id": "unique-id",
    "company": "Acme Corp",
    "role": "Senior DevOps Engineer",
    "jd": "full job description text",
    "dateApplied": "2024-01-15",
    "status": "Interview",
    "followUpDate": "2024-01-22",
    "notes": "Good culture fit",
    "tailoredCV": "markdown CV text",
    "coverLetter": "cover letter text",
    "emailDraft": "outreach email",
    "skills": ["Kubernetes", "Terraform", "AWS"],
    "atsScore": 85,
    "baseCvVersion": "2024-01-15T10:30:00Z"
  }
]
```

### Interview Questions (localStorage key: `runbook`)
```json
{
  "Acme Corp — Senior DevOps Engineer": [
    {
      "id": "unique-id",
      "question": "How do you handle a production outage?",
      "type": "behavioral",
      "round": "Round 1",
      "outcome": "strong",
      "notes": "Focused on communication and root cause analysis",
      "date": "2024-01-18"
    }
  ]
}
```

### Base CV (localStorage key: `base-cv`)
- Raw text (markdown or plain text format)

### Base CV Timestamp (localStorage key: `base-cv-timestamp`)
- ISO date when profile was last saved (for version tracking)

---

## Tips & Best Practices

### 🔧 **Setup Optimization**
- Use a fast model if Ollama is slow: try `ollama pull neural-chat` (smaller, faster)
- On Mac with Apple Silicon, Ollama is very fast
- First generation takes longer (model loading), subsequent ones are quicker

### 📋 **CV Tips**
- Keep your base CV **complete** (all roles, skills, certifications)
- Include quantified metrics (increased performance by 40%, managed team of 5, etc.)
- List all technologies you know (tailoring engine will pick relevant ones)
- Use clear section headers: Summary, Skills, Experience, Certifications

### 🎯 **Application Tips**
- Paste the **full** job description (not just the title)
- Log applications immediately after sending (or bulk-import later)
- Use follow-up date field to remind yourself (overdue dates turn red)
- Mark "Rejected" or "Ghosted" so they don't clutter your active pipeline

### 🎤 **Interview Tips**
- Log questions **during or right after** the interview (freshest memory)
- Use "Notes" to capture your thinking, what went well, what to improve
- Mark outcomes to track which topics you're strongest/weakest on
- Review runbook by company before each round

---

## Limitations & Known Issues

### ⚠️ **Current Limitations**
- **No cloud sync** — data only lives in your browser
- **No multi-device sync** — export/import manually if you want to move data
- **No bulk export** — runbook and applications stored as JSON in localStorage
- **Ollama required for CV generation** — local LLM only (no cloud LLM integration)
- **ATS score is an estimate** — real ATS systems are proprietary; this is a good proxy

### 🐛 **Known Issues**
- If browser tab is closed abruptly during save, last change may be lost
- Very large CVs (>20,000 words) may slow down tailoring
- Some DOCX files with complex formatting may lose formatting on import (text only)

---

## What's Next?

### Planned Features
- CSV/JSON export of all applications
- Analytics dashboard (success rate, time-to-offer, company stats)
- Bulk actions (mark multiple apps as rejected)
- Email templates (auto-send with tailored CV)
- Interview prep: link runbook questions to each JD

### Contributing
This is a personal project. If you want to add features:
1. Edit `careerops.html` for frontend changes
2. Edit `backend.py` for backend changes
3. Test locally before merging
4. Keep data models backwards-compatible

---

## Support

### Debug mode
Open browser DevTools (F12) and check Console for errors:
```javascript
// Check what's stored:
console.log(JSON.parse(localStorage.getItem('app-log')))
console.log(JSON.parse(localStorage.getItem('runbook')))
```

### Export your data (backup)
```javascript
// In browser console:
copy(JSON.stringify({
  applications: JSON.parse(localStorage.getItem('app-log')),
  runbook: JSON.parse(localStorage.getItem('runbook')),
  baseCv: localStorage.getItem('base-cv')
}, null, 2))
```

Then paste into a `.json` file to save.

---

**Happy job hunting! 🚀**
