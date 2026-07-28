#!/usr/bin/env python3
import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

app = Flask(__name__)
CORS(app)

OLLAMA_BASE = os.environ.get('OLLAMA_BASE', 'http://localhost:11434')
MODEL = os.environ.get('OLLAMA_MODEL', 'mistral')

def check_ollama():
    try:
        r = requests.get(f'{OLLAMA_BASE}/api/tags', timeout=2)
        return r.status_code == 200
    except:
        return False

@app.route('/api/health', methods=['GET'])
def health():
    ollama_running = check_ollama()
    return jsonify({
        'status': 'ok',
        'ollama': 'connected' if ollama_running else 'disconnected',
        'model': MODEL,
        'docx_support': DOCX_AVAILABLE
    })

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

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        if not check_ollama():
            return jsonify({
                'error': 'Ollama not running',
                'hint': 'Start Ollama with: ollama serve'
            }), 503

        data = request.json
        system = data.get('system', '')
        user_msg = data.get('user_message', '')

        # Build messages for Ollama API (OpenAI-compatible)
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': user_msg})

        response = requests.post(
            f'{OLLAMA_BASE}/v1/chat/completions',
            headers={'Content-Type': 'application/json'},
            json={
                'model': MODEL,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 8000,
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
    port = int(os.environ.get('FLASK_PORT', 5000))

    print(f"🔍 Looking for Ollama at {OLLAMA_BASE}...")
    if not check_ollama():
        print("❌ Ollama is not running!")
        print("\n📦 Setup steps:")
        print("  Terminal 1: ollama serve")
        print("  Terminal 2 (this script): python3 backend.py")
        print("  Terminal 3: python3 -m http.server 8000")
        print("\nIf first time:")
        print("  ollama pull mistral")
        exit(1)

    print("✅ Ollama connected!")
    print(f"📦 Using model: {MODEL}")
    print(f"🚀 Backend running on http://localhost:{port}")
    print(f"📄 Frontend: http://localhost:8000/careerops.html")
    print(f"✓ Health check: http://localhost:{port}/api/health")
    app.run(port=port, debug=False)
