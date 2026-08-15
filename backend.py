#!/usr/bin/env python3
import os
import re
import json
import hmac
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

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
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize DynamoDB using the standard AWS credential provider chain.
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    applications_table = dynamodb.Table('applications')
    runbook_table = dynamodb.Table('runbook')
    DYNAMODB_AVAILABLE = True
except Exception as e:
    print(f"⚠️  DynamoDB initialization failed: {e}")
    DYNAMODB_AVAILABLE = False

# Initialize S3 client for CV file storage.
S3_BUCKET = 'careerops-589535355002'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}
ALLOWED_CONTENT_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

try:
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    S3_AVAILABLE = True
except Exception as e:
    print(f"⚠️  S3 initialization failed: {e}")
    S3_AVAILABLE = False

def dynamodb_safe(value):
    """Convert JSON payloads into DynamoDB-compatible values."""
    return json.loads(json.dumps(value), parse_float=Decimal)

def json_safe(value):
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return value

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


def validate_cv_file(file):
    """Validate an uploaded CV file. Returns (None) on success or (error_message) on failure."""
    if not file or not file.filename:
        return 'No file provided'

    # Check extension
    filename = os.path.basename(file.filename or '')
    filename = re.sub(r'[^\w\-.]', '_', filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f'Invalid file type. Allowed formats: {", ".join(sorted(ALLOWED_EXTENSIONS))}'

    # Check Content-Type matches extension
    expected_content_type = ALLOWED_CONTENT_TYPES.get(ext)
    if file.content_type != expected_content_type:
        return f'Content-Type mismatch. Expected {expected_content_type} for {ext} file'

    # Check file size (read content to verify)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size == 0:
        return 'File is empty'

    if size > MAX_FILE_SIZE:
        return f'File too large. Maximum size is 5 MB'

    return None


# ========== APPLICATIONS API ==========

@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Get all applications for a user"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        user_id = request.args.get('userId', 'default-user')
        response = applications_table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        items = json_safe(response.get('Items', []))
        # Sort by dateApplied descending
        items = sorted(items, key=lambda x: x.get('dateApplied', ''), reverse=True)
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications', methods=['POST'])
def create_application():
    """Create or update an application"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        data = request.json
        user_id = data.get('userId', 'default-user')
        
        item = {
            'userId': user_id,
            'id': data.get('id'),
            'company': data.get('company'),
            'role': data.get('role'),
            'jd': data.get('jd', ''),
            'status': data.get('status', 'Applied'),
            'dateApplied': data.get('dateApplied'),
            'followUpDate': data.get('followUpDate', ''),
            'atsScore': data.get('atsScore'),
            'skills': data.get('skills', []),
            'notes': data.get('notes', ''),
            'emailSubject': data.get('emailSubject', ''),
            'emailTo': data.get('emailTo', ''),
            'tailoredCV': data.get('tailoredCV', ''),
            'coverLetter': data.get('coverLetter', ''),
            'emailDraft': data.get('emailDraft', ''),
            'baseCvVersion': data.get('baseCvVersion', ''),
            'timestamp': int(datetime.now(timezone.utc).timestamp())
        }

        # Preserve CV file metadata if present in request data
        if data.get('cvFilename'):
            item['cvFilename'] = data['cvFilename']
        if data.get('cvS3Key'):
            item['cvS3Key'] = data['cvS3Key']
        
        applications_table.put_item(Item=dynamodb_safe(item))
        return jsonify({'status': 'ok', 'id': data.get('id')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/<app_id>', methods=['PUT'])
def update_application(app_id):
    """Update an application"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        data = request.json
        user_id = data.get('userId', 'default-user')
        
        # Get existing item
        response = applications_table.get_item(
            Key={'userId': user_id, 'id': app_id}
        )
        existing = response.get('Item', {})
        
        # Merge with new data
        item = {**existing, **data}
        item['timestamp'] = int(datetime.now(timezone.utc).timestamp())
        
        applications_table.put_item(Item=dynamodb_safe(item))
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/<app_id>', methods=['DELETE'])
def delete_application(app_id):
    """Delete an application"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        user_id = request.args.get('userId', 'default-user')
        applications_table.delete_item(
            Key={'userId': user_id, 'id': app_id}
        )
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== CV UPLOAD API ==========

@app.route('/api/applications/<app_id>/cv', methods=['POST'])
def upload_cv(app_id):
    """Upload a CV file for a specific application"""
    if not S3_AVAILABLE:
        return jsonify({'error': 'Storage service is unavailable'}), 503

    # Extract userId from form data
    user_id = request.form.get('userId')
    if not user_id:
        return jsonify({'error': 'userId is required'}), 400

    # Get the uploaded file
    file = request.files.get('file')

    # Validate the file
    validation_error = validate_cv_file(file)
    if validation_error:
        return jsonify({'error': validation_error}), 400

    # Verify the application exists for this user in DynamoDB
    try:
        response = applications_table.get_item(
            Key={'userId': user_id, 'id': app_id}
        )
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    item = response.get('Item')
    if not item:
        return jsonify({'error': 'Application not found'}), 404

    # Check userId ownership
    if item.get('userId') != user_id:
        return jsonify({'error': 'Insufficient permissions'}), 403

    # Upload file to S3
    filename = os.path.basename(file.filename or '')
    filename = re.sub(r'[^\w\-.]', '_', filename)
    s3_key = f"{user_id}/{app_id}/{filename}"

    try:
        file.seek(0)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file.read(),
            ContentType=file.content_type
        )
    except Exception as e:
        return jsonify({'error': 'Failed to upload file to storage'}), 503

    # Update DynamoDB record with CV metadata
    try:
        applications_table.update_item(
            Key={'userId': user_id, 'id': app_id},
            UpdateExpression='SET cvS3Key = :s3key, cvFilename = :fname',
            ExpressionAttributeValues={
                ':s3key': s3_key,
                ':fname': filename
            }
        )
    except Exception as e:
        return jsonify({'error': f'Failed to update application record: {str(e)}'}), 500

    return jsonify({
        'status': 'ok',
        'filename': filename,
        's3Key': s3_key
    }), 200


@app.route('/api/applications/<app_id>/cv', methods=['GET'])
def download_cv(app_id):
    """Download a CV file for a specific application"""
    if not S3_AVAILABLE:
        return jsonify({'error': 'Storage service is unavailable'}), 503

    # Extract userId from query parameter
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'error': 'userId is required'}), 400

    # Verify the application exists for this user in DynamoDB
    try:
        response = applications_table.get_item(
            Key={'userId': user_id, 'id': app_id}
        )
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    item = response.get('Item')
    if not item:
        return jsonify({'error': 'Application not found'}), 404

    # Check userId ownership
    if item.get('userId') != user_id:
        return jsonify({'error': 'Insufficient permissions'}), 403

    # Check that CV metadata exists
    s3_key = item.get('cvS3Key')
    filename = item.get('cvFilename')
    if not s3_key or not filename:
        return jsonify({'error': 'No CV associated with this application'}), 404

    # Generate pre-signed URL
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=900  # 15 minutes
        )
        return jsonify({
            'url': url,
            'filename': filename
        }), 200
    except s3_client.exceptions.NoSuchKey:
        return jsonify({'error': 'CV file not found in storage'}), 404
    except Exception as e:
        if 'NoSuchKey' in str(e):
            return jsonify({'error': 'CV file not found in storage'}), 404
        return jsonify({'error': 'Failed to generate download link'}), 503


@app.route('/api/applications/<app_id>/cv', methods=['DELETE'])
def delete_cv(app_id):
    """Delete a CV file for a specific application"""
    if not S3_AVAILABLE:
        return jsonify({'error': 'Storage service is unavailable'}), 503

    # Extract userId from query parameter
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'error': 'userId is required'}), 400

    # Verify the application exists for this user in DynamoDB
    try:
        response = applications_table.get_item(
            Key={'userId': user_id, 'id': app_id}
        )
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    item = response.get('Item')
    if not item:
        return jsonify({'error': 'Application not found'}), 404

    # Check userId ownership
    if item.get('userId') != user_id:
        return jsonify({'error': 'Insufficient permissions'}), 403

    # Check that CV metadata exists
    s3_key = item.get('cvS3Key')
    if not s3_key:
        return jsonify({'error': 'No CV associated with this application'}), 404

    # Delete from S3
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
    except Exception as e:
        return jsonify({'error': 'Failed to delete file from storage'}), 503

    # Remove CV metadata from DynamoDB
    try:
        applications_table.update_item(
            Key={'userId': user_id, 'id': app_id},
            UpdateExpression='REMOVE cvS3Key, cvFilename'
        )
    except Exception as e:
        return jsonify({'error': f'Partial failure: CV deleted from storage but metadata update failed: {str(e)}'}), 500

    return jsonify({'status': 'ok'}), 200


# ========== RUNBOOK API ==========

@app.route('/api/runbook', methods=['GET'])
def get_runbook():
    """Get all runbook questions for a user"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        user_id = request.args.get('userId', 'default-user')
        response = runbook_table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        items = json_safe(response.get('Items', []))
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/runbook', methods=['POST'])
def create_question():
    """Add an interview question to runbook"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        data = request.json
        user_id = data.get('userId', 'default-user')
        
        item = {
            'userId': user_id,
            'id': data.get('id'),
            'roleKey': data.get('roleKey', ''),
            'question': data.get('question'),
            'type': data.get('type'),
            'round': data.get('round'),
            'outcome': data.get('outcome'),
            'notes': data.get('notes', ''),
            'date': data.get('date'),
            'suggestions': data.get('suggestions'),
            'timestamp': int(datetime.now(timezone.utc).timestamp())
        }
        
        runbook_table.put_item(Item=dynamodb_safe(item))
        return jsonify({'status': 'ok', 'id': data.get('id')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/runbook/<question_id>', methods=['PUT'])
def update_question(question_id):
    """Update a runbook question"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        data = request.json
        user_id = data.get('userId', 'default-user')
        
        # Get existing item
        response = runbook_table.get_item(
            Key={'userId': user_id, 'id': question_id}
        )
        existing = response.get('Item', {})
        
        # Merge with new data
        item = {**existing, **data}
        item['timestamp'] = int(datetime.now(timezone.utc).timestamp())
        
        runbook_table.put_item(Item=dynamodb_safe(item))
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/runbook/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Delete a runbook question"""
    if not DYNAMODB_AVAILABLE:
        return jsonify({'error': 'DynamoDB not available'}), 503
    
    try:
        user_id = request.args.get('userId', 'default-user')
        runbook_table.delete_item(
            Key={'userId': user_id, 'id': question_id}
        )
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== HEALTH CHECK ==========

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        ollama_running = check_ollama()
        
        # Test DynamoDB connection
        dynamodb_status = 'disconnected'
        if DYNAMODB_AVAILABLE:
            try:
                applications_table.table_status
                dynamodb_status = 'connected'
            except:
                dynamodb_status = 'disconnected'
        
        return jsonify({
            'status': 'ok',
            'ollama': 'connected' if ollama_running else 'disconnected',
            'model': MODEL,
            'dynamodb': dynamodb_status,
            'docx_support': DOCX_AVAILABLE
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========== LOGIN ==========

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

# ========== DOCX SUPPORT ==========

@app.route('/api/extract-docx', methods=['POST'])
def extract_docx():
    if not DOCX_AVAILABLE:
        return jsonify({'error': 'python-docx not installed'}), 400
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
        
        from docx import Document
        doc = Document(file)
        text = '\n'.join([para.text for para in doc.paragraphs])
        
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== LLM GENERATION ==========

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        system = data.get('system', '')
        user_msg = data.get('user_message', '')
        model = data.get('model', MODEL)

        ollama_base = resolve_ollama_base(request.headers.get('X-Ollama-Base'))

        if not check_ollama_at(ollama_base):
            return jsonify({
                'error': 'Ollama not running',
                'hint': f'Start Ollama with: ollama serve (at {ollama_base})'
            }), 503

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

        result = response.json()
        message_content = result['choices'][0]['message']['content']

        def fix_json_strings(s):
            def escape_inner(m):
                inner = m.group(1)
                inner = inner.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                return '"' + inner + '"'
            return re.sub(r'"((?:[^"\\]|\\.)*)"', escape_inner, s, flags=re.DOTALL)

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
    
    if DYNAMODB_AVAILABLE:
        print(f"\n🔍 Checking DynamoDB...")
        try:
            applications_table.table_status
            print("✅ DynamoDB connected!")
        except Exception as e:
            print(f"⚠️  DynamoDB connection error: {e}")
    else:
        print("\n⚠️  DynamoDB not available")
    
    print(f"📦 Using model: {MODEL}")
    print(f"🚀 Backend running on http://localhost:{port}")
    print(f"📄 Frontend: http://localhost:8000/careerops.html")
    print(f"✓ Health check: http://localhost:{port}/api/health")
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(host=host, port=port, debug=debug)
