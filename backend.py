#!/usr/bin/env python3
import os
import re
import json
import hmac
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

app = Flask(__name__)
CORS(app)

OLLAMA_BASE = (
    os.environ.get('OLLAMA_BASE')
    or os.environ.get('OLLAMA_URL')
    or os.environ.get('OLLAMA_HOST')
    or 'http://localhost:11434'
)
MODEL = os.environ.get('OLLAMA_MODEL', 'mistral')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
TRANSCRIPTION_MODEL = os.environ.get('OPENAI_TRANSCRIPTION_MODEL', 'gpt-4o-mini-transcribe')
REQUIRE_OLLAMA_ON_START = os.environ.get('REQUIRE_OLLAMA_ON_START', '').lower() in ('1', 'true', 'yes')
CAREEROPS_USERNAME = os.environ.get('CAREEROPS_USERNAME', '')
CAREEROPS_PASSWORD = os.environ.get('CAREEROPS_PASSWORD', '')

def check_ollama():
    return check_ollama_at(OLLAMA_BASE)

def check_ollama_at(base_url):
    try:
        r = requests.get(f'{base_url}/api/tags', timeout=2)
        return r.status_code == 200
    except:
        return False

def resolve_ollama_base(header_base=None):
    header_base = (header_base or '').strip()
    if not header_base:
        return OLLAMA_BASE
    if 'localhost' in header_base and 'localhost' not in OLLAMA_BASE:
        return OLLAMA_BASE
    return header_base

@app.route('/api/login', methods=['POST'])
def login():
    if not CAREEROPS_PASSWORD:
        return jsonify({'error': 'Login is not configured'}), 503

    data = request.json or {}
    username = str(data.get('username', ''))
    password = str(data.get('password', ''))

    if (
        hmac.compare_digest(username, CAREEROPS_USERNAME)
        and hmac.compare_digest(password, CAREEROPS_PASSWORD)
    ):
        return jsonify({'ok': True, 'username': username})

    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/health', methods=['GET'])
def health():
    ollama_running = check_ollama()
    return jsonify({
        'status': 'ok',
        'ollama': 'connected' if ollama_running else 'disconnected',
        'model': MODEL,
        'transcription_model': TRANSCRIPTION_MODEL,
        'transcription_api': 'configured' if OPENAI_API_KEY else 'missing_api_key',
        'docx_support': DOCX_AVAILABLE
    })

@app.route('/api/generate-docx', methods=['POST'])
def generate_docx():
    if not DOCX_AVAILABLE:
        return jsonify({'error': 'python-docx not installed'}), 400
    try:
        from io import BytesIO
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        import copy

        data = request.json or {}
        cv_text = data.get('cv_text', '')
        if not cv_text.strip():
            return jsonify({'error': 'No CV text provided'}), 400

        doc = Document()

        # Page margins
        for section in doc.sections:
            section.top_margin = Inches(0.7)
            section.bottom_margin = Inches(0.7)
            section.left_margin = Inches(0.85)
            section.right_margin = Inches(0.85)

        def add_hr(paragraph):
            p = paragraph._p
            pPr = p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), '1E3C37')
            pBdr.append(bottom)
            pPr.append(pBdr)

        def set_spacing(paragraph, before=0, after=0, line=None):
            from docx.oxml.ns import qn
            pPr = paragraph._p.get_or_add_pPr()
            pSpacing = OxmlElement('w:spacing')
            pSpacing.set(qn('w:before'), str(before))
            pSpacing.set(qn('w:after'), str(after))
            if line:
                pSpacing.set(qn('w:line'), str(line))
                pSpacing.set(qn('w:lineRule'), 'auto')
            pPr.append(pSpacing)

        lines = cv_text.split('\n')
        saw_name = False
        contact_done = False

        for raw_line in lines:
            line = raw_line.strip()

            # H1 — Name
            if line.startswith('# '):
                content = line[2:].replace('**', '')
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                set_spacing(p, before=0, after=40)
                run = p.add_run(content)
                run.bold = True
                run.font.size = Pt(18)
                run.font.color.rgb = RGBColor(25, 25, 25)
                saw_name = True
                continue

            # Contact line
            if saw_name and not contact_done and line and len(line) < 300 and (
                '@' in line or '|' in line or 'linkedin' in line.lower() or line.startswith('http')):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                set_spacing(p, before=0, after=60)
                run = p.add_run(line.replace('**', ''))
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(80, 80, 80)
                contact_done = True
                continue

            # H2 — Section header
            if line.startswith('## '):
                content = line[3:].replace('**', '').upper()
                p = doc.add_paragraph()
                set_spacing(p, before=120, after=40)
                run = p.add_run(content)
                run.bold = True
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor(30, 60, 55)
                add_hr(p)
                continue

            # H3 — Job title line
            if line.startswith('### '):
                content = line[4:].replace('**', '')
                # Split off trailing (date) if present
                date_part = ''
                title_part = content
                m = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', content)
                if m:
                    title_part = m.group(1).strip()
                    date_part = m.group(2).strip()

                p = doc.add_paragraph()
                set_spacing(p, before=80, after=20, line=276)
                # Title run
                run_t = p.add_run(title_part)
                run_t.bold = True
                run_t.font.size = Pt(10)
                run_t.font.color.rgb = RGBColor(25, 25, 25)
                # Date run — right-aligned via tab stop
                if date_part:
                    from docx.oxml import OxmlElement
                    from docx.oxml.ns import qn
                    from docx.shared import Inches
                    pPr = p._p.get_or_add_pPr()
                    tabs = OxmlElement('w:tabs')
                    tab = OxmlElement('w:tab')
                    tab.set(qn('w:val'), 'right')
                    tab.set(qn('w:pos'), '8640')  # ~6 inches from left margin
                    tabs.append(tab)
                    pPr.append(tabs)
                    run_tab = p.add_run('\t')
                    run_date = p.add_run(date_part)
                    run_date.font.size = Pt(9)
                    run_date.font.color.rgb = RGBColor(100, 100, 100)
                continue

            # Bullet
            if line.startswith('- ') or line.startswith('* '):
                content = line[2:].replace('**', '')
                p = doc.add_paragraph(style='List Bullet')
                set_spacing(p, before=0, after=20, line=252)
                run = p.add_run(content)
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(35, 35, 35)
                continue

            # Empty line
            if not line:
                continue

            # Plain text
            p = doc.add_paragraph()
            set_spacing(p, before=0, after=20, line=252)
            run = p.add_run(line.replace('**', ''))
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(40, 40, 40)

        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)
        return send_file(
            buf,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name='CV.docx'
        )
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/api/extract-docx', methods=['POST'])
def extract_docx():
    if not DOCX_AVAILABLE:
        return jsonify({
            'error': 'DOCX support not installed',
            'hint': 'Install with: pip install python-docx'
        }), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.docx'):
        return jsonify({'error': 'Please upload a .docx file'}), 400

    try:
        doc = Document(file)
        text = '\n'.join([para.text for para in doc.paragraphs])
        if not text.strip():
            return jsonify({
                'error': 'Could not extract text from DOCX',
                'hint': 'Try re-saving the file or copy-pasting manually'
            }), 400
        return jsonify({
            'text': text,
            'filename': file.filename
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to read DOCX: {str(e)}'
        }), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    if not OPENAI_API_KEY:
        return jsonify({
            'error': 'OpenAI API key not configured',
            'hint': 'Set OPENAI_API_KEY in the backend environment'
        }), 503

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400

        files = {
            'file': (
                file.filename,
                file.stream,
                file.mimetype or 'application/octet-stream'
            )
        }
        data = {
            'model': TRANSCRIPTION_MODEL,
            'language': 'en',
            'response_format': 'json'
        }
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }

        response = requests.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            return jsonify({
                'error': 'Transcription API request failed',
                'detail': detail
            }), response.status_code

        result = response.json()
        return jsonify({
            'transcription': result.get('text', ''),
            'language': 'en',
            'model': TRANSCRIPTION_MODEL,
            'usage': result.get('usage')
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        system = data.get('system', '')
        user_msg = data.get('user_message', '')
        model = data.get('model', MODEL)

        # Allow frontend to override Ollama base via header
        ollama_base = resolve_ollama_base(request.headers.get('X-Ollama-Base'))

        if not check_ollama_at(ollama_base):
            return jsonify({
                'error': 'Ollama not running',
                'hint': f'Start Ollama with: ollama serve (at {ollama_base})'
            }), 503

        # Build messages for Ollama API (OpenAI-compatible)
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': user_msg})

        response = requests.post(
            f'{ollama_base}/v1/chat/completions',
            headers={'Content-Type': 'application/json'},
            json={
                'model': model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 12000,
                'stream': False
            },
            timeout=180
        )

        if response.status_code != 200:
            return jsonify({
                'error': f'Ollama error: {response.status_code}',
                'detail': response.text
            }), response.status_code

        data = response.json()

        # Convert Ollama response to Anthropic format
        message_content = data['choices'][0]['message']['content']

        # The LLM may produce JSON with raw control characters inside string values.
        # Attempt to fix by escaping unescaped control chars within quoted strings.
        def fix_json_strings(s):
            """Escape raw control characters inside JSON string values."""
            def escape_inner(m):
                inner = m.group(1)
                inner = inner.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                return '"' + inner + '"'
            # Match JSON strings: opening quote, content (non-quote or escaped char), closing quote
            return re.sub(r'"((?:[^"\\]|\\.)*)"', escape_inner, s, flags=re.DOTALL)

        # Try parsing as-is first; if it fails, attempt to fix control characters
        stripped = message_content.strip()
        if stripped.startswith('```'):
            stripped = re.sub(r'^```(?:json)?\s*', '', stripped)
            stripped = re.sub(r'```\s*$', '', stripped).strip()
        try:
            json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            stripped = fix_json_strings(stripped)

        return jsonify({
            'content': [{'type': 'text', 'text': stripped}]
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Ollama request timed out (model may still be loading)'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5001))

    print(f"🔍 Looking for Ollama at {OLLAMA_BASE}...")
    if not check_ollama():
        print("⚠️  Ollama is not running!")
        print("\n📦 Setup steps:")
        print("  Terminal 1: ollama serve")
        print("  Terminal 2 (this script): python3 backend.py")
        print("  Terminal 3: python3 -m http.server 8000")
        print("\nIf first time:")
        print("  ollama pull mistral")
        if REQUIRE_OLLAMA_ON_START:
            exit(1)
    else:
        print("✅ Ollama connected!")
    print(f"📦 Using model: {MODEL}")
    print(f"🚀 Backend running on http://localhost:{port}")
    print(f"📄 Frontend: http://localhost:8000/careerops.html")
    print(f"✓ Health check: http://localhost:{port}/api/health")
    app.run(host="0.0.0.0", port=port, debug=False)
