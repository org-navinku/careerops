# CareerOps Quick Reference Guide

## 🎯 The 5-Minute Workflow

### Step 1: Set Up Your Base Profile (1 min)
```
Tab 4: BASE PROFILE
├─ Upload PDF or DOCX (drag & drop)
│  └─ Or paste your CV text manually
├─ Review extracted text
└─ Click "Save base profile"

✓ Status pill shows "base profile loaded"
```

### Step 2: Generate Tailored CV for a Job (2 min)
```
Tab 1: DEPLOY
├─ Paste the full job description
├─ Click "Generate application package"
│  └─ LLM tailors your CV (30-60s)
├─ **NEW:** See ATS score
│  ├─ ✅ 80+ = Green = Download confidently
│  ├─ 🟠 60-79 = Amber = Review keywords
│  └─ ❌ <60 = Red = ⚠️ WARNING - Consider editing
├─ Review matched/missing keywords
├─ (Optional) Edit CV, click "rescore edits"
└─ Download PDF (CV + cover letter + email draft)
```

### Step 3: Track Your Application (30 sec)
```
Tab 1: DEPLOY
└─ Click "Log this application →"

Tab 2: PIPELINE
├─ Application appears in table
├─ Auto-filled: company, role, ATS score, date applied
└─ You can edit: status, follow-up date, notes
```

### Step 4: Log Interview Questions (1 min per question)
```
Tab 3: RUNBOOK
├─ Select company/role or type custom
├─ Add question type (Tech/Behavioral/System Design/Leadership)
├─ Add interview round (Phone/Round 1/Round 2/Final)
├─ Paste the question
├─ Add your answer/notes
├─ Mark outcome (Strong/Okay/Weak/Follow-up)
└─ Click "Add to runbook"

Filter by company to prep for next round!
```

---

## 📱 Tab Navigation

### Tab 1: Deploy
**Use when:** You found a job you want to apply to  
**What it does:** Tailors your CV to match the JD, generates cover letter & email  
**Output:** PDF CV, ATS score, cover letter, email draft  
**Key feature NEW:** ⚠️ ATS warning if score < 80

### Tab 2: Pipeline
**Use when:** You need to track your applications  
**What it does:** Shows all companies/roles you've applied to, their status, follow-up dates  
**What you can do:** Edit status, mark follow-ups, delete entries  
**Key feature:** Red highlights for overdue follow-ups

### Tab 3: Runbook
**Use when:** You want to prep for interviews  
**What it does:** Logs every question you're asked, organized by company/role  
**What you can do:** Filter by company, track question types, record outcomes  
**Key feature NEW:** Color-coded badges for question type + outcome

### Tab 4: Base Profile
**Use when:** You want to update your master CV  
**What it does:** Upload/paste your master CV that gets tailored for each job  
**File support:** PDF ✓ | DOCX ✓ | Text paste ✓  
**Key feature NEW:** Automatically extracts text from DOCX files

---

## 🎮 UI Components Explained

### Upload Zone (Tab 4)
```
┌─────────────────────────────────────┐
│ Drop a PDF or DOCX here or          │  ← NEW: DOCX support!
│ click to browse                      │
└─────────────────────────────────────┘
```
- Drag-and-drop enabled
- Click to browse file
- Auto-extracts text from PDF/DOCX
- Shows word count when done

### ATS Score Display (Tab 1)
```
Original:
┌──────────┐  Matched: ✓ kubernetes, terraform
│   --     │  Missing: docker, ci/cd, monitoring
└──────────┘

NEW if score < 80:
┌──────────────────────────────────────┐
│ ⚠️ ATS Score Below Target (75/100)   │
│ This CV may not clear automated      │
│ screening. Consider editing to       │
│ include more missing keywords.       │
└──────────────────────────────────────┘
```

### Application Row (Tab 2)
```
Company: [Acme Corp________]  Role: [Senior DevOps_____]  ATS: [87]
Applied: [2024-01-15]  Status: [Screening▼]  Follow-up: [2024-01-22]
Notes: [Liked my incident response...]  [✕]
```
- All fields editable, auto-saves
- Follow-up date turns red when due
- Click ✕ to delete

### Question Item (Tab 3) - NEW!
```
Acme Corp — Senior DevOps Engineer
┌────────────────────────────────────────────────┐
│ 2024-01-18  ▪ [Tech] [Phone Screen] [STRONG] ✕│
│                                                │
│ Q: Describe your approach to troubleshooting  │
│    latency issues in production.              │
│                                                │
│ > Your approach: Systematic - start with      │
│   metrics, isolate layer, verify fix...       │
└────────────────────────────────────────────────┘

Color legend:
[Tech] = blue (teal)
[STRONG] = green
[WEAK] = red
[OKAY] = amber
```

---

## 💾 Where Is My Data Saved?

All data is stored **locally in your browser** using localStorage:

| Key | What | Location |
|-----|------|----------|
| `base-cv` | Your master CV text | Browser localStorage |
| `base-cv-timestamp` | When it was saved | Browser localStorage |
| `app-log` | All applications | Browser localStorage |
| `runbook` | Interview questions | Browser localStorage |

**Privacy:** ✅ Everything stays on your machine. No cloud, no analytics, no tracking.

**Backup:** Export your data
```javascript
// In browser console (F12):
copy(JSON.stringify({
  applications: JSON.parse(localStorage.getItem('app-log')),
  runbook: JSON.parse(localStorage.getItem('runbook')),
  baseCv: localStorage.getItem('base-cv')
}, null, 2))
// Then paste into a .json file
```

---

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Focus search | Ctrl+F (browser search) |
| Edit inline | Click the field |
| Save | Auto-saves on blur |
| Submit form | Enter or click button |
| Tab navigation | Click tab button |
| Delete | Click ✕ button |

---

## 🔴 Common Issues & Fixes

### "Ollama not running"
**Fix:** Start Ollama in a separate terminal
```bash
ollama serve
ollama pull mistral  # First time only
```

### "Cannot reach backend"
**Fix:** Start backend in a separate terminal
```bash
cd /Users/navinkumar/workrepos/pers-prj/careerops
source venv/bin/activate
python3 backend.py
```

### "PDF upload failed"
**Reason:** PDF is scanned images (no text layer)  
**Fix:** Paste the CV text manually or re-export from Word

### "DOCX upload failed"
**Reason:** DOCX is corrupted or has unsupported formatting  
**Fix:** Re-save in Word/Google Docs or paste text manually

### "Data not saving"
**Reason:** Browser localStorage is disabled or full  
**Fix:** 
- Disable private browsing mode
- Clear browser cache
- Try a different browser

### "ATS score is low"
**Reason:** Missing keywords from JD that aren't in your CV  
**Fix:** Manually edit CV to naturally include relevant skills you have

---

## 📊 Application Status Guide

| Status | Meaning | Action |
|--------|---------|--------|
| **Applied** | Sent application | Wait for response |
| **Screening** | Resume reviewed, under consideration | Wait 1-2 weeks |
| **Interview** | Interview scheduled or completed | Prepare, follow-up after |
| **Offer** | Job offer received | Celebrate! ✓ |
| **Rejected** | Application rejected | Mark and move on |
| **Ghosted** | No response after weeks | Mark and move on |

---

## 🎤 Interview Outcome Meanings

| Outcome | Meaning | Next Step |
|---------|---------|-----------|
| **Strong** | Went well, positive feedback | Expect follow-up or offer |
| **Okay** | Neutral, could go either way | Wait for decision |
| **Weak** | Didn't go as expected | Plan improvements for next time |
| **Follow-up** | Interviewer asked follow-up | Prepare answer, email followup |

---

## 📝 Question Type Guide

| Type | Example | Use For |
|------|---------|---------|
| **Technical** | "Explain REST APIs" | Coding, architecture, tools |
| **Behavioral** | "Tell me about conflict" | Soft skills, past situations |
| **System Design** | "Design a URL shortener" | Architecture, scalability |
| **Leadership** | "How do you mentor?" | Management, team skills |
| **Other** | Anything else | Edge cases |

---

## 🚀 Pro Tips

### Tip 1: Upload Complete CV
Include everything: all roles, all skills, certifications, projects. Tailoring works best with complete source material.

### Tip 2: Use Quantified Metrics
Instead of: "Improved performance"  
Use: "Improved performance by 40% (from 500ms to 300ms)"

Tailoring engine loves numbers for ATS scoring.

### Tip 3: Watch Your ATS Score
- Score 80+: Likely to pass ATS filters ✓
- Score 60-79: May pass, may fail 🟠
- Score <60: Probably won't pass ❌

If low, edit the CV to naturally include missing keywords.

### Tip 4: Log Questions Immediately
Log runbook questions right after interview (memory is fresh). Include:
- Exact question (or as close as you remember)
- Your approach/answer
- What you'd do differently next time

### Tip 5: Prep Before Round 2
Before next interview at same company:
- Tab 3 → Select company → Review all past questions
- Spot patterns in what they ask
- Practice those types of questions

### Tip 6: Regular Cleanup
Once a week:
- Tab 2 → Mark rejected/ghosted applications
- Clears visual clutter
- Stats dashboard stays accurate

---

## 📈 Typical Workflow by Phase

### Phase 1: Job Hunt (Weeks 1-4)
```
Daily:
- Find JD → Tab 1 → Generate → Download → Apply
- Evening: Log to Pipeline

Weekly:
- Review Pipeline, mark follow-ups
- Check Runbook if had interviews
```

### Phase 2: Active Interviews (Weeks 4-8)
```
After each interview:
- Tab 3 → Log the questions
- Tab 2 → Update status to "Interview"
- Tab 2 → Set follow-up date (usually 1 week later)

Before each round:
- Tab 3 → Filter by company → Review questions
- Tab 1 → (If new JD) Generate and review CV
```

### Phase 3: Offers & Decisions (Weeks 8+)
```
When offer comes:
- Tab 2 → Mark as "Offer"
- Tab 2 → Add notes (comp, title, start date)

Mark others as rejected:
- Tab 2 → Multi-select or individual ✕
- Cleans up pipeline

Celebrate! 🎉
```

---

## 🔗 File Structure

```
/Users/navinkumar/workrepos/pers-prj/careerops/
├── careerops.html          ← Open this in browser
├── backend.py              ← Python server (handles DOCX, Ollama)
├── requirements.txt        ← pip install -r requirements.txt
├── SETUP.md               ← Full installation guide
├── FEATURES.md            ← What's implemented & roadmap
├── QUICK_REFERENCE.md     ← This file
├── IMPLEMENTATION_SUMMARY.md ← What was built
└── venv/                  ← Python virtual environment
```

---

## 🎓 Learning Resources

### Inside the App
- **Status pill** — Green = ready to use, tells you what's configured
- **Toast notifications** — Success/error messages (bottom of screen)
- **Muted notes** — Help text under fields
- **Tooltips** — Hover over badges for descriptions

### Documentation Files
- **SETUP.md** — Complete guide (troubleshooting, configuration)
- **FEATURES.md** — What's implemented, what's coming
- **IMPLEMENTATION_SUMMARY.md** — Technical details

---

## ✅ Checklist: First-Time Setup

- [ ] Read SETUP.md
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Start Ollama: `ollama serve`
- [ ] Start backend: `python3 backend.py`
- [ ] Start web server: `python3 -m http.server 8000`
- [ ] Open browser: `http://localhost:8000/careerops.html`
- [ ] Tab 4: Upload/paste your CV
- [ ] Tab 1: Paste a job description, generate CV
- [ ] Check ATS score (should be shown)
- [ ] Tab 2: Log the application
- [ ] Tab 3: Add a sample interview question
- [ ] Refresh page: Data persists ✓

---

## 📞 Support

### Debug Mode
Press F12 → Console → Run:
```javascript
// Check what's stored
console.log(JSON.parse(localStorage.getItem('app-log')))

// Check Ollama status
fetch('http://localhost:5000/api/health').then(r=>r.json()).then(console.log)
```

### Export Data (Backup)
```javascript
copy(JSON.stringify({
  applications: JSON.parse(localStorage.getItem('app-log')),
  runbook: JSON.parse(localStorage.getItem('runbook')),
  baseCv: localStorage.getItem('base-cv')
}, null, 2))
// Then paste into a .json file
```

### Clear Data (Fresh Start)
```javascript
// In browser console:
localStorage.clear()
location.reload()
```

---

**Happy job hunting! 🚀**

*For detailed guides, see SETUP.md, FEATURES.md, and IMPLEMENTATION_SUMMARY.md*
