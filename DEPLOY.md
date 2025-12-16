# Deployment Guide

## Quick Deploy to Your GitHub Account

### Step 1: Create Repository on GitHub
1. Go to https://github.com/new
2. Repository name: `Jira-AI-Agent`
3. Description: "AI-powered JIRA ticket analysis agent for Critical Ops support"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Update Remote and Push

Replace `YOUR_USERNAME` with your GitHub username:

```bash
# Update remote URL
git remote set-url origin https://github.com/YOUR_USERNAME/Jira-AI-Agent.git

# Push to your repository
git push -u origin main
```

### Step 3: Verify Deployment

Visit: `https://github.com/YOUR_USERNAME/Jira-AI-Agent`

## What's Included

✅ Complete JIRA AI Agent codebase
✅ Enhanced with McKinsey-style consultant responses
✅ Improved ticket import functionality
✅ All documentation (README, SETUP_GUIDE, USER_GUIDE)
✅ Proper .gitignore (excludes sensitive files)

## Important Notes

- **API Keys**: Never commit `.env` files or API keys
- **Configuration**: Users must create their own `backend/.env` file with:
  - JIRA_URL
  - JIRA_USERNAME
  - JIRA_API_TOKEN
  - GEMINI_API_KEY
  - COHERE_API_KEY (if using Cohere embeddings)

## Repository Structure

```
Jira-AI-Agent/
├── backend/          # Flask backend and Celery workers
├── frontend.py        # Streamlit frontend
├── weaviate/         # Weaviate database setup
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```

