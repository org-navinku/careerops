# Interview Recording & AI Coaching Feature

## 🎯 Overview

CareerOps now includes an end-to-end interview recording workflow that automatically:
1. **Transcribes** interview audio using Whisper AI
2. **Extracts** questions and answers from the transcript
3. **Provides** AI coaching suggestions on your answers
4. **Saves** everything to your runbook for future reference

This lets you learn from every interview and continuously improve.

---

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
pip install openai-whisper==20231117

# Install system dependency (FFmpeg)
# macOS:
brew install ffmpeg

# Ubuntu:
sudo apt-get install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
```

### Basic Workflow (5 minutes)
1. **Record interview** using Zoom, QuickTime, phone recorder, or any app
2. Open **CareerOps** → Go to **Runbook tab (Tab 3)**
3. Scroll to **"Auto-extract from recording"**
4. **Drag & drop** your recording (MP3, WAV, M4A, etc.)
5. Review the **transcription** and **extracted Q&A**
6. Click **"Get better answer suggestions"** (optional)
7. Select the questions you want
8. Pick the company/role
9. Click **"Import to runbook"**
10. Done! ✅ Questions saved with coaching

---

## 📋 Step-by-Step Guide

### Step 1: Record Your Interview

Use any recording tool:
- **Zoom**: Settings → Recording → Record to this computer
- **Mac QuickTime**: File → New Audio Recording
- **iPhone**: Voice Memos app
- **Android**: Google Recorder
- **Audacity**: Open source recorder

**Tips:**
- Position microphone close to capture both speakers clearly
- Minimize background noise (quiet room)
- Test audio quality before the interview

### Step 2: Upload Recording

1. Open **CareerOps** in your browser
2. Click **Tab 3: Runbook**
3. Scroll down to **"Auto-extract from recording"**
4. **Option A:** Drag & drop your audio file
5. **Option B:** Click the zone and browse for the file

**Supported formats:** MP3, WAV, M4A, OGG, WebM, or any format FFmpeg supports

### Step 3: Review Transcription

The recording will be transcribed automatically:
- First run: Takes 30 seconds to 2+ minutes (Whisper downloads ~140MB model)
- Subsequent runs: Usually 2-5 minutes
- Output: Full interview transcript displayed

**What to look for:**
- ✅ Accuracy: Is the transcription readable?
- ⚠️ Garbled parts: May indicate audio quality issues
- 💡 Use this as reference, not gospel

### Step 4: Review Extracted Q&A

CareerOps automatically extracts questions and answers:

```
Extracted Q&A Example:
✅ Q: Tell me about your experience with Kubernetes
   A: I've been working with Kubernetes for 3 years, deployed 
      15+ clusters in production...
   
✅ Q: How do you handle failures?
   A: I implemented monitoring and alerting, response time <5min...
```

**What you can do:**
- ☑️ Check/uncheck questions you want to keep
- ✏️ Edit questions or answers if auto-extraction was imperfect
- 🏷️ Change question type (Technical, Behavioral, etc.)
- ❌ Delete any that don't make sense

### Step 5: Get AI Coaching (Optional)

For selected questions, get AI-powered feedback:

1. **Select** the questions you want coaching on (checkboxes)
2. Click **"Get better answer suggestions"**
3. Wait for LLM analysis (~30-60 seconds)
4. Review suggestions:

```
Q: Tell me about handling a production incident
Your answer: We diagnosed the issue, isolated root cause, deployed fix
Feedback: Good structure! Add communication & post-mortem details.
Better answer: I'd:
  1) Alert team & stakeholders (communication first)
  2) Gather metrics & logs (systematic diagnosis)
  3) Isolate root cause
  4) Deploy fix with testing
  5) Run post-mortem & document
```

**Coaching includes:**
- ✅ What your answer did well
- 🔧 What could be improved
- 💡 A more complete answer
- 📚 Framework & structure tips

### Step 6: Import to Runbook

1. **Choose company/role** from dropdown or type custom
2. **Select questions** you want to import (checkboxes)
3. Click **"Import selected to runbook"**
4. Done! Questions saved with:
   - Your answers
   - Question types
   - AI coaching suggestions

### Step 7: Review Coaching Anytime

Navigate to **Runbook tab** → **Browse section**:

```
Acme Corp — Senior Engineer
├─ Q: Tell me about handling production incidents
│  └─ Your answer: We diagnosed...
│  └─ 💡 Coach feedback: Good structure! Add communication...
│  └─ Better answer: I'd alert team first, then...
│
└─ Q: Biggest technical challenge?
   └─ Your answer: Migrating legacy monolith...
   └─ 💡 Coach feedback: Great example! Add measurable impact...
   └─ Better answer: We migrated a 10M LOC monolith...
```

Coaching feedback appears inline when viewing questions!

---

## 🎓 How the AI Coach Works

### Q&A Extraction
The LLM analyzes the transcript to:
- ✅ Identify question boundaries
- ✅ Link questions to answers
- ✅ Detect question type
- ✅ Extract concise Q&A pairs

**Output:** Structured JSON with questions, answers, and types

### Coaching Analysis
The LLM coach reviews your answers to:
- ✅ Assess how well you addressed the question
- ✅ Identify key strengths in your response
- ✅ Suggest improvements
- ✅ Provide a more complete answer

**Output:** Detailed feedback with better answer suggestions

---

## 📊 Data Storage & Privacy

### What's Stored?
- ✅ Questions & your answers
- ✅ Question types (Technical, Behavioral, etc.)
- ✅ AI coaching suggestions
- ✅ Date & interview round
- ✅ Interview outcome (Strong/Weak/etc.)

### Where It's Stored?
- ✅ Browser `localStorage` (on your computer)
- ❌ NOT in cloud
- ❌ NOT on CareerOps servers
- ❌ NOT sent to external services

### Privacy & Security
- 🔒 Transcription: Local (Whisper runs on your machine)
- 🔒 Q&A extraction: Local (Ollama backend)
- 🔒 Coaching: Local (Ollama backend)
- 🔒 No audio/transcripts ever leave your machine
- 🔒 No tracking, analytics, or logging

**Backup your data:**
```javascript
// In browser console (F12):
copy(JSON.stringify({
  runbook: JSON.parse(localStorage.getItem('runbook'))
}, null, 2))
// Paste into a .json file to backup
```

---

## ⚠️ Troubleshooting

### "Whisper not installed" error
**Solution:** Install Whisper
```bash
pip install openai-whisper==20231117
```

### Transcription is very slow or fails
**Reason:** FFmpeg missing or model not downloaded  
**Solution:**
```bash
# macOS
brew install ffmpeg

# Ubuntu  
sudo apt-get install ffmpeg

# Windows: Download from https://ffmpeg.org
```

### Transcription is inaccurate or garbled
**Reason:** Poor audio quality  
**Solution:**
- Record in a quiet room
- Position microphone close to speakers
- Test audio before recording
- Use higher quality recording format

### Q&A extraction produces no results
**Reason:** Transcript not good enough or LLM had issues  
**Solution:**
- Review the transcription (is it readable?)
- Manually add questions to runbook
- Try shorter/clearer recordings

### Coaching suggestions are off-topic
**Reason:** LLM misunderstood or answers were unclear  
**Solution:**
- Treat suggestions as guidance, not gospel
- Use what's helpful, ignore what isn't
- Coaching improves with practice

---

## 📈 Best Practices

### Recording
- ✅ Record full interviews (not just your answers)
- ✅ Ensure clear audio (test beforehand)
- ✅ Quiet room with good microphone
- ✅ Save as MP3 or WAV (smaller files)

### Q&A Review
- ✅ Review transcription for accuracy
- ✅ Edit extracted Q&A for clarity
- ✅ Remove non-question sections (e.g., chitchat)
- ✅ Correct types if auto-detection was wrong

### Coaching
- ✅ Get suggestions for key questions
- ✅ Review suggestions with an open mind
- ✅ Note patterns (what types do you struggle with?)
- ✅ Practice the "better answers" before next interview

### Preparation
- ✅ Browse past questions before your next interview
- ✅ Review coaching suggestions to refresh memory
- ✅ Filter by question type to focus areas
- ✅ Build a personal interview playbook

---

## 🔧 Technical Details

### Frontend Architecture
```
recordingZone (UI)
  ├─ handleRecordingFile() → uploads audio
  ├─ extractQAFromTranscription() → calls LLM
  ├─ renderExtractedQA() → shows UI
  └─ showSuggestions() → displays coaching

Data flow:
Audio file → Whisper (backend) → Transcript
Transcript → LLM (extraction) → Q&A pairs
Q&A → LLM (coaching) → Suggestions
Suggestions → localStorage → Runbook
```

### Backend Architecture
```
/api/transcribe
  ├─ Input: multipart/form-data {file: audio}
  ├─ Process: whisper.load_model('base')
  ├─ Output: {transcription, language}
  └─ Cleanup: Auto-remove temp files

Whisper model:
  • Size: ~140MB
  • Downloads: First run only (~5 minutes)
  • Languages: All languages (optimized for English)
  • Accuracy: ~95% for clear English audio
```

### LLM Integration
```
Q&A Extraction:
  • Prompt: Analyze transcript for Q&A pairs
  • Response: JSON {questions, answers, types}
  • Backend: Ollama (configurable in Settings)
  
Coaching Analysis:
  • Prompt: Review answers for feedback
  • Response: JSON {feedback, betterAnswer} per Q
  • Backend: Ollama (configurable in Settings)
```

---

## 🚀 Performance

| Task | Time | Notes |
|------|------|-------|
| First transcription | 30s - 2min | Model download (~140MB) |
| Subsequent transcription | 2-5 min | Depends on audio length |
| Q&A extraction | 10-30s | LLM processing |
| Coaching suggestions | 30-60s | LLM processing |
| **Total first time** | **~10 minutes** | Mostly Whisper setup |
| **Subsequent interviews** | **5-7 minutes** | Much faster |

---

## 🎯 Use Cases

### 1. After Each Interview
Record your interviews and extract Q&A immediately:
- Capture questions while fresh
- Get coaching feedback
- Build runbook for future rounds

### 2. Interview Prep
Before interviewing with the same company:
- Browse past questions you've been asked
- Review AI coaching suggestions
- Practice better answers
- Identify patterns (types you're weak on)

### 3. Career Development
Over time, track your interview performance:
- Which question types are you strong at?
- How has your answer quality improved?
- Build a personal coaching archive
- Track trends in hiring (popular questions)

### 4. Team Learning
(Future) Share recordings with peers:
- Practice group interviews
- Get multiple perspectives on answers
- Build team interview playbook
- Shared coaching insights

---

## 📚 Example Interview Archive

After using CareerOps for a few months:

```
Acme Corp — Senior Engineer (3 rounds)
├─ Technical Q&A (with coaching)
├─ System Design (with coaching)
└─ Behavioral Q&A (with coaching)

Widgets Inc — Staff Engineer (1 round phone)
├─ Technical Q&A (with coaching)
└─ Culture fit (with coaching)

StartupXYZ — Engineering Lead (multiple rounds)
├─ Technical Q&A (with coaching)
├─ Leadership Q&A (with coaching)
└─ Project deep-dive (with coaching)

Analytics:
├─ Strongest: Technical questions (feedback 80+ score)
├─ Growing: Leadership questions (improved over time)
├─ Need work: System design (lower scores, need practice)
└─ Trending: More system design questions in market
```

---

## 🔮 Future Enhancements

- [ ] Video recording support (extract audio)
- [ ] Speaker identification (interviewer vs candidate)
- [ ] Timestamp tracking (link feedback to moments)
- [ ] Batch processing (multiple recordings)
- [ ] PDF export (study guide from suggestions)
- [ ] Analytics dashboard (question type trends)
- [ ] Peer sharing (compare answers)
- [ ] Interview practice mode (get coached in real-time)

---

## 📞 Support

### Check these first:
1. Is FFmpeg installed? `ffmpeg -version`
2. Is Whisper installed? `pip list | grep whisper`
3. Is Ollama running? Check Settings tab → Test connection
4. Is audio format supported? Try MP3 or WAV

### Debug in browser:
```javascript
// Check localStorage
console.log(JSON.parse(localStorage.getItem('runbook')))

// Check for errors
// Open DevTools (F12) → Console → look for error messages
```

### Common issues:
- See SETUP.md → Troubleshooting section
- See QUICK_REFERENCE.md → UI guide

---

## 📖 Learn More

- **Getting Started:** [START_HERE.md](START_HERE.md)
- **Full Setup:** [SETUP.md](SETUP.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **All Features:** [FEATURES.md](FEATURES.md)

---

**Happy interviewing! 🎙️ Every recording is an opportunity to learn. 📚**
