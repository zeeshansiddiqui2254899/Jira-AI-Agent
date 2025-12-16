# 🚀 JIRA AI Agent - Setup Guide

## Current Project Status
Your JIRA AI Agent project is well-structured and almost ready to run! Here's what you need to do next.

---

## ✅ Step-by-Step Setup Instructions

### 1. **Create Environment Configuration File**

Create a `.env` file in the `backend/` directory with your credentials:

```bash
cd backend
touch .env
```

Add the following content to `backend/.env`:

```env
# Jira Configuration
JIRA_URL="https://your-domain.atlassian.net"
JIRA_USERNAME="your-email@example.com"
JIRA_API_TOKEN="your-jira-api-token"

# Cohere API Key (for embeddings)
COHERE_API_KEY="your-cohere-api-key"
```

**How to get these:**
- **JIRA_API_TOKEN**: Go to https://id.atlassian.com/manage-profile/security/api-tokens
- **COHERE_API_KEY**: Sign up at https://cohere.com/ and get your API key from the dashboard

---

### 2. **Install Python Dependencies**

```bash
# From project root
pip install -r requirements.txt
```

---

### 3. **Start Redis Server**

Redis is required for Celery task queue management.

**On macOS:**
```bash
# Install Redis if not already installed
brew install redis

# Start Redis server
brew services start redis
# OR run directly:
redis-server
```

**On Linux:**
```bash
sudo apt-get install redis-server
sudo service redis-server start
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

---

### 4. **Start Weaviate Database**

Weaviate stores your Jira ticket embeddings.

```bash
cd weaviate
docker-compose up -d
```

**Verify Weaviate is running:**
```bash
curl http://localhost:8080/v1/.well-known/ready
# Should return: {"ready":true}
```

---

### 5. **Set Up Weaviate Schema**

Create the database schema for storing Jira issues:

```bash
cd weaviate
python setup_schema.py
```

This creates the `JiraIssue` collection with all necessary properties.

---

### 6. **Start Ollama (AI Model)**

Ollama provides the AI model for generating responses.

**Option A: Using Docker (Recommended)**
```bash
docker run -d -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull tinyllama
```

**Option B: Install Ollama directly**
- Download from: https://ollama.ai/
- Install and run: `ollama serve`
- Pull the model: `ollama pull tinyllama`

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
# Should return list of available models
```

---

### 7. **Start the Backend Services**

You need to start both Celery worker and Flask server.

**Option A: Using the provided script (Linux/macOS)**
```bash
cd backend
chmod +x start_server.sh
./start_server.sh
```

**Option B: Manual start (Recommended for development)**

**Terminal 1 - Start Celery Worker:**
```bash
cd backend
celery -A celery_app worker --loglevel=info
```

**Terminal 2 - Start Flask Server:**
```bash
cd backend
gunicorn -c gunicorn_config.py app:app
# OR for development:
python -m flask run --port=5000
```

---

### 8. **Set Up ngrok (for Jira Webhooks)**

Jira webhooks require HTTPS. Use ngrok to expose your local server:

```bash
# Install ngrok if not installed
# macOS: brew install ngrok
# Or download from: https://ngrok.com/

# Start ngrok tunnel
ngrok http 5000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) - you'll need this for Jira webhook configuration.

---

### 9. **Configure Jira Webhook**

1. Go to your Jira project → **Settings** → **System** → **Webhooks**
2. Create a new webhook with:
   - **Name**: JIRA AI Agent
   - **URL**: `https://your-ngrok-url.ngrok.io/webhook/jira`
   - **Events**: Select "Issue updated" → Filter: "Status changed to Closed"

---

## 🧪 Testing Your Setup

### Test 1: Check Backend Health
```bash
curl http://localhost:5000/api/query -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

### Test 2: Test Celery Worker
```bash
cd backend
python -c "from tasks import test_task; print(test_task.delay().get())"
```

### Test 3: Test Weaviate Connection
```bash
cd weaviate
python test/verify_schema.py
```

---

## 📋 Quick Checklist

- [ ] Created `.env` file with all required keys
- [ ] Installed Python dependencies (`pip install -r requirements.txt`)
- [ ] Redis is running (`redis-cli ping`)
- [ ] Weaviate is running (`docker-compose up` in `weaviate/`)
- [ ] Weaviate schema is created (`python setup_schema.py`)
- [ ] Ollama is running with `tinyllama` model
- [ ] Celery worker is running
- [ ] Flask server is running on port 5000
- [ ] ngrok tunnel is active (for webhooks)
- [ ] Jira webhook is configured

---

## 🐛 Common Issues & Solutions

### Issue: "Connection refused" to Redis
**Solution**: Make sure Redis is running: `redis-server` or `brew services start redis`

### Issue: "Cannot connect to Weaviate"
**Solution**: 
- Check Docker is running: `docker ps`
- Start Weaviate: `cd weaviate && docker-compose up -d`

### Issue: "COHERE_API_KEY not found"
**Solution**: 
- Make sure `.env` file exists in `backend/` directory
- Check the path in `weaviate_service.py` matches your `.env` location

### Issue: "Ollama connection refused"
**Solution**: 
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check the Ollama endpoint URL in `tasks.py` matches your setup

### Issue: Celery tasks not executing
**Solution**: 
- Make sure Celery worker is running: `celery -A celery_app worker --loglevel=info`
- Check Redis connection: `redis-cli ping`

---

## 🎯 Next Steps After Setup

1. **Test with a real Jira ticket**: Close a test ticket in Jira and verify it's stored in Weaviate
2. **Test query endpoint**: Send queries to `/api/query` and verify AI responses
3. **Monitor logs**: Check Celery worker logs for any errors
4. **Add more data**: Process more closed tickets to build your knowledge base

---

## 📚 Project Structure Overview

```
Jira-AI-Agent/
├── backend/
│   ├── app.py              # Flask API endpoints
│   ├── celery_app.py       # Celery configuration
│   ├── tasks.py            # Background tasks (webhook processing, queries)
│   ├── config.py           # Configuration settings
│   ├── .env                # Environment variables (CREATE THIS)
│   └── services/
│       ├── jira_service.py      # Jira API integration
│       ├── weaviate_service.py  # Weaviate database operations
│       └── query_service.py     # Query processing (currently commented)
├── weaviate/
│   ├── docker-compose.yml  # Weaviate Docker setup
│   └── setup_schema.py    # Database schema creation
└── requirements.txt        # Python dependencies
```

---

## 💡 Development Tips

1. **Use separate terminals** for Celery worker and Flask server during development
2. **Check logs** regularly - Celery worker logs show task execution details
3. **Test incrementally** - Test each service individually before testing the full flow
4. **Monitor Weaviate** - Use Weaviate's GraphQL interface at `http://localhost:8080/v1/graphql` to inspect stored data

---

## 🆘 Need Help?

If you encounter issues:
1. Check the logs (Celery worker, Flask server, Docker containers)
2. Verify all services are running (Redis, Weaviate, Ollama)
3. Ensure `.env` file has correct credentials
4. Test each component individually

Good luck! 🚀



