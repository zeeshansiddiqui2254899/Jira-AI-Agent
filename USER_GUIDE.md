# 🎫 JIRA AI Agent - User Guide

## 📍 How to Access Your Ticket Insights

### 🌐 **Option 1: Web Interface (Easiest Way)**

I've created a beautiful web interface for you! Here's how to access it:

1. **Open your web browser** and go to:
   ```
   http://localhost:8501
   ```

2. **You'll see a clean interface** where you can:
   - Type questions about your support tickets
   - Get instant AI-powered insights
   - See relevant ticket information

3. **Example Questions to Try:**
   - "How do we handle login issues?"
   - "What are common payment problems?"
   - "Show me tickets about API errors"
   - "How do we resolve authentication errors?"

---

### 💻 **Option 2: Using the API Directly**

If you prefer using command line or integrating with other tools:

#### **Query Your Tickets:**
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do we handle login issues?"}'
```

#### **Check Webhook Status:**
```bash
curl -X POST http://localhost:5000/webhook/jira \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

---

## 🎯 What You Can Do

### 1. **Search Ticket Insights**
   - Ask questions in natural language
   - Get AI-powered summaries of similar tickets
   - Find patterns and solutions from past tickets

### 2. **View Ticket Patterns**
   - See common issues and their resolutions
   - Understand trends in support requests
   - Get actionable insights for your team

### 3. **Automatic Ticket Collection**
   - When you close a ticket in Jira (CO project), it's automatically stored
   - No manual work needed!
   - The system learns from every closed ticket

---

## 🚀 Quick Start Guide

### **Step 1: Start the Web Interface**
```bash
cd /Users/zeeshansiddiqui/Jira-AI-Agent
python3 -m streamlit run frontend.py
```

Then open: **http://localhost:8501**

### **Step 2: Ask Your First Question**
Type a question like:
- "What are the most common issues we see?"
- "How do we resolve payment errors?"
- "Show me tickets about API problems"

### **Step 3: Get Insights**
The AI will:
1. Search through all your Critical Ops tickets
2. Find the most relevant ones
3. Generate insights and solutions

---

## 📊 Understanding the Results

When you ask a question, you'll get:

- **Summary**: AI-generated insights based on similar tickets
- **Patterns**: Common issues and their solutions
- **References**: Relevant ticket information
- **Actionable Insights**: What to do next

---

## 🔍 What Tickets Are Included?

**Only tickets from:**
- ✅ Project: **CO** (Critical Ops)
- ✅ Status: **Closed**
- ✅ Automatically collected via webhooks

**Excluded:**
- ❌ Tickets from other projects
- ❌ Open/In Progress tickets (until they're closed)

---

## 💡 Tips for Best Results

1. **Be Specific**: Instead of "errors", ask "authentication errors"
2. **Use Keywords**: Include relevant terms like "payment", "login", "API"
3. **Ask Follow-ups**: Build on previous questions for deeper insights
4. **Check Regularly**: More closed tickets = better insights

---

## 🛠️ Troubleshooting

### **Web Interface Not Loading?**
- Make sure Streamlit is running: `ps aux | grep streamlit`
- Check if port 8501 is available
- Restart: `python3 -m streamlit run frontend.py`

### **No Results Found?**
- Make sure you have closed tickets in the CO project
- Check if webhooks are configured in Jira
- Verify tickets are being stored (check Celery logs)

### **Backend Not Responding?**
- Check if Flask is running: `ps aux | grep gunicorn`
- Verify Celery worker: `ps aux | grep celery`
- Check logs: `tail -f backend/celery.log`

---

## 📱 Access from Other Devices

If you want to access from your phone or another computer:

1. **Find your local IP:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **Access via:**
   ```
   http://YOUR_IP_ADDRESS:8501
   ```

3. **Make sure your firewall allows connections**

---

## 🎨 Features

- ✅ Beautiful, easy-to-use web interface
- ✅ Natural language queries
- ✅ AI-powered insights
- ✅ Focused on Critical Ops tickets only
- ✅ Real-time search results
- ✅ Mobile-friendly design

---

## 📞 Need Help?

- Check the logs: `tail -f backend/celery.log`
- Verify services are running
- Make sure your backend is on: `http://localhost:5000`

Enjoy exploring your ticket insights! 🚀


