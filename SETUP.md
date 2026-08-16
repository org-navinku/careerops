# CareerOps Setup Guide

## Prerequisites

- **Python 3.8+**
- **AWS credentials** configured (`~/.aws/credentials` or env vars) for DynamoDB and S3
- **Modern browser** (Chrome, Safari, Firefox, Edge)

---

## Installation

### 1. Clone and set up

```bash
cd /path/to/careerops
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create DynamoDB tables

```bash
./deploy-dynamodb.sh
```

This creates the `applications`, `runbook`, and `llm-providers` tables.

### 3. Set environment variables

```bash
export AWS_REGION=us-east-1
export CAREEROPS_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Optional: login auth
export CAREEROPS_USERNAME=your-username
export CAREEROPS_PASSWORD=your-password
```

> **Important:** Save your `CAREEROPS_ENCRYPTION_KEY` — it encrypts LLM API keys at rest. If you lose it, you'll need to re-enter your API keys in Settings.

### 4. Start the backend

```bash
source venv/bin/activate
python3 backend.py
```

Output: `🚀 Backend running on http://localhost:5001`

### 5. Start the web server

```bash
python3 -m http.server 8000
```

### 6. Open browser

```
http://localhost:8000/careerops.html
```

---

## LLM Provider Configuration

CV tailoring requires an LLM provider. Configure it in the app's **Settings** tab:

### OpenAI
1. Get an API key from [platform.openai.com](https://platform.openai.com)
2. In Settings, add provider: Type = OpenAI, paste your API key
3. Model: `gpt-4o-mini` (fast/cheap) or `gpt-4o` (best quality)

### Anthropic
1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. In Settings, add provider: Type = Custom, base URL = `https://api.anthropic.com/v1`
3. Model: `claude-sonnet-4-20250514`

### Custom (OpenAI-compatible)
Works with any OpenAI-compatible endpoint (LM Studio, Ollama, vLLM, etc.):
1. In Settings, add provider: Type = Custom
2. Set base URL (e.g., `http://localhost:11434/v1` for Ollama)
3. Set model name

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot reach backend" | Ensure `python3 backend.py` is running on port 5001 |
| "DynamoDB not available" | Check AWS credentials: `aws sts get-caller-identity` |
| "Encryption key" warning | Set `CAREEROPS_ENCRYPTION_KEY` env var |
| CV generation fails | Check LLM provider is configured in Settings tab |
| PDF upload shows no text | PDF may be image-only; paste text manually |
| DOCX upload fails | Re-save in Word/Docs, or paste text manually |

### Debug commands

```bash
# Check backend health
curl http://localhost:5001/api/health

# Check DynamoDB access
curl 'http://localhost:5001/api/applications?userId=default-user'

# Check backend logs
# Backend prints detailed logs to stdout
```

---

## Running Tests

```bash
source venv/bin/activate
python3 -m pytest tests/ -q          # Quick summary
python3 -m pytest tests/ -v          # Verbose
python3 -m pytest tests/ -x          # Stop on first failure
```

---

## Docker Deployment

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for container deployment instructions.

```bash
docker-compose up --build    # Local
./scripts/push-to-ecr.sh    # Push to AWS ECR
```

---

## Data Backup

```bash
# Export applications
aws dynamodb scan --table-name applications --region $AWS_REGION --output json > applications-backup.json

# Export runbook
aws dynamodb scan --table-name runbook --region $AWS_REGION --output json > runbook-backup.json
```
