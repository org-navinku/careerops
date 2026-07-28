# 🚀 START HERE

## ✅ Good News: App is Ready!

The web interface is **running now** at:
```
http://localhost:8000/careerops.html
```

You can:
- ✅ Upload your CV (PDF or DOCX)
- ✅ View all 4 tabs (Deploy, Pipeline, Runbook, Profile)
- ✅ Browse the UI and features
- ✅ Read all the documentation

**You just need to start 2 more services to unlock AI features:**

---

## 🔧 To Enable AI CV Tailoring (5 minutes)

You need Ollama (local LLM) and the backend running.

### Terminal 1: Start Ollama
```bash
ollama serve

# First time only:
ollama pull mistral
```

Expected output:
```
Listening on 127.0.0.1:11434 (compute)
```

### Terminal 2: Start Backend
```bash
cd /Users/navinkumar/workrepos/pers-prj/careerops
source venv/bin/activate
python3 backend.py
```

Expected output:
```
✅ Ollama connected!
🚀 Backend running on http://localhost:5000
```

### Done!
Now refresh: http://localhost:8000/careerops.html

You'll see:
- Tab 1 (Deploy) will be fully functional
- CV generation will work
- ATS scoring will work

---

## 📊 What Works Right Now (Without Backend)

✅ **Tab 4: Base Profile**
- Upload PDF or DOCX
- View extracted text
- Paste CV manually
- Data saves locally

✅ **Tab 2: Pipeline** (after logging)
- Track applications
- Edit status & follow-ups
- Add notes
- See stats

✅ **Tab 3: Runbook** (after logging)
- Log interview questions
- Tag by type & round
- Track outcomes
- Filter by company

❌ **Tab 1: Deploy** (needs backend)
- Will show error: "Cannot reach backend"
- Start backend to enable

---

## 🎯 Test Now (2 minutes)

1. Open: http://localhost:8000/careerops.html
2. Go to **Tab 4: Base Profile**
3. Paste your CV (or use sample text)
4. Click "Save base profile"
5. See the status change to "base profile loaded"
6. Try **Tab 2: Pipeline** - manually add an application
7. Try **Tab 3: Runbook** - log a sample question

Everything works! Data persists in your browser.

---

## 🎓 Full Feature List

### Available Now
- ✅ CV upload (PDF + DOCX)
- ✅ Manual CV entry
- ✅ Application pipeline tracking
- ✅ Interview question logging
- ✅ Data persistence (localStorage)
- ✅ All UI/UX features

### Available With Backend
- ✅ CV generation from JD
- ✅ ATS scoring
- ✅ PDF export
- ✅ Cover letter generation
- ✅ Email draft generation

---

## 📚 Documentation

| When | Read |
|------|------|
| Want quick overview | [README.md](README.md) (5 min) |
| Ready to set up backend | [SETUP.md](SETUP.md) (10 min) |
| Want to use features | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (10 min) |
| Need navigation help | [INDEX.md](INDEX.md) (2 min) |

---

## ⚡ Quick Commands

### Check what's running
```bash
lsof -i :8000    # Web server (should show: LISTEN)
lsof -i :5000    # Backend (should show: LISTEN if running)
lsof -i :11434   # Ollama (should show: LISTEN if running)
```

### Kill a service if stuck
```bash
lsof -i :8000 | grep -oE "^[^ ]+" | tail -1 | xargs kill -9
```

### Debug browser
Open DevTools: Press F12
- Console tab: See any errors
- Application tab: View localStorage data

---

## 🎁 You Have

✅ Full working app (4 tabs, all UI)
✅ 7 comprehensive documentation files
✅ Interactive startup script
✅ Python virtual environment ready
✅ All code and configuration
✅ Git history (8 commits)

---

## 🚀 Next Steps

### Option A: Just Explore (Right Now)
1. Open: http://localhost:8000/careerops.html
2. Try Tab 4 (upload CV)
3. Try Tab 2 & 3 (log application & question)
4. See data persist after refresh

### Option B: Full Setup (5 minutes)
1. Open Terminal 1: `ollama serve`
2. Open Terminal 2: `python3 backend.py`
3. Refresh browser
4. Test Tab 1 (CV generation)

### Option C: Learn First (15 minutes)
1. Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. Then follow Option A or B

---

## ✅ Verification Checklist

Run these in Terminal to verify setup:

```bash
# Check if app loads
curl -s http://localhost:8000/careerops.html | head -5

# Check if backend would work (when started)
# curl http://localhost:5000/api/health

# Check Python dependencies
python3 -c "import flask, docx; print('✓ OK')"

# Check venv
ls -la venv/bin/python
```

---

**You're all set! Start with http://localhost:8000/careerops.html 🎉**

For any questions, see the documentation files above.
