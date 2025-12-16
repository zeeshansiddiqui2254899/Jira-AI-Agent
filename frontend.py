import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="SubcontractorHub - JIRA AI Agent",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme and modern design
st.markdown("""
    <style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        min-height: 100vh;
        padding: 0;
    }
    
    /* Header styling */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 2rem;
        background: rgba(0, 0, 0, 0.3);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .logo-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: white;
    }
    
    .logo-text {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    
    /* Main content area */
    .main-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: calc(100vh - 200px);
        padding: 3rem 2rem;
        text-align: center;
    }
    
    .large-logo {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .greeting {
        font-size: 1.5rem;
        color: #e0e0e0;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .subtitle {
        font-size: 1rem;
        color: #b0b0b0;
        margin-bottom: 2rem;
        line-height: 1.6;
        max-width: 600px;
    }
    
    /* Input container */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(26, 26, 26, 0.95);
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem 2rem;
        z-index: 1000;
    }
    
    .input-wrapper {
        max-width: 800px;
        margin: 0 auto;
        position: relative;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        color: #e0e0e0;
        font-size: 1rem;
        width: 100%;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #888888;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Results container */
    .results-container {
        max-width: 900px;
        margin: 2rem auto;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .result-title {
        font-size: 1.25rem;
        color: #ffffff;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .result-content {
        color: #d0d0d0;
        line-height: 1.8;
        font-size: 0.95rem;
    }
    
    .ticket-reference {
        background: rgba(102, 126, 234, 0.1);
        border-left: 3px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        color: #b0b0b0;
        font-size: 0.9rem;
    }
    
    .disclaimer {
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.75rem;
        color: #888888;
        text-align: center;
        z-index: 999;
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-online {
        background: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    }
    
    .status-offline {
        background: #ef4444;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header-container">
        <div class="logo-container">
            <div class="logo-icon">🎫</div>
            <div class="logo-text">SubcontractorHub</div>
        </div>
        <div style="color: #888; font-size: 0.9rem;">JIRA AI Agent</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar for configuration (minimized)
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input(
        "Backend API URL",
        value="http://localhost:5000",
        help="URL where your Flask backend is running"
    )
    
    st.markdown("---")
    st.header("📊 System Status")
    
    # Check backend status
    try:
        response = requests.get(f"{api_url}/api/query", timeout=2)
        status_class = "status-online"
        status_text = "🟢 Online"
    except:
        status_class = "status-offline"
        status_text = "🔴 Offline"
    
    st.markdown(f'<span class="status-indicator {status_class}"></span><span style="color: #e0e0e0;">Backend: {status_text}</span>', unsafe_allow_html=True)

# Main content area - centered like Sense AI
st.markdown("""
    <div class="main-content">
        <div class="large-logo">🎫</div>
        <div class="greeting">Hi, Welcome to SubcontractorHub AI Agent</div>
        <div class="subtitle">
            Ready to help you find solutions from your Critical Ops support tickets? 
            Ask me about past incidents, resolutions, and best practices. 
            I'll analyze our complete ticket history to provide comprehensive, consultant-level insights.
        </div>
    </div>
""", unsafe_allow_html=True)

# Input area at bottom (fixed position)
st.markdown('<div class="input-container">', unsafe_allow_html=True)

# Query input
user_query = st.text_input(
    "",
    placeholder="Ask me anything about Critical Ops tickets...",
    key="query_input",
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    search_button = st.button("🔍 Search Tickets", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Disclaimer
st.markdown("""
    <div class="disclaimer">
        SubcontractorHub AI Agent may contain errors. We recommend verifying important information with your team.
    </div>
""", unsafe_allow_html=True)

# Display results
if search_button or user_query:
    if not user_query.strip():
        st.warning("⚠️ Please enter a question to search.")
    else:
        with st.spinner("🔍 Analyzing tickets and generating insights..."):
            try:
                # Make API request
                response = requests.post(
                    f"{api_url}/api/query",
                    json={"query": user_query},
                    timeout=300
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'success':
                        summary = data.get('summary', 'No summary available')
                        
                        # Check if no relevant tickets were found
                        if "no such incident has occurred before" in summary.lower() or "reach out to the respective poc" in summary.lower():
                            st.markdown("""
                                <div class="results-container">
                                    <div class="result-title">⚠️ No Similar Incidents Found</div>
                                    <div class="result-content">{}</div>
                                </div>
                            """.format(summary.replace('\n', '<br>')), unsafe_allow_html=True)
                        else:
                            st.markdown("""
                                <div class="results-container">
                                    <div class="result-title">📋 Resolution Guide</div>
                                    <div class="result-content">{}</div>
                                </div>
                            """.format(summary.replace('\n', '<br>')), unsafe_allow_html=True)
                            
                            # Show ticket references if available
                            ticket_keys = data.get('ticket_keys', [])
                            if ticket_keys:
                                ticket_list = ", ".join(ticket_keys[:10])
                                if len(ticket_keys) > 10:
                                    ticket_list += f" and {len(ticket_keys) - 10} more"
                                st.markdown(f"""
                                    <div class="ticket-reference">
                                        📎 Based on analysis of tickets: <strong>{ticket_list}</strong>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.error(f"❌ Error: {data.get('message', 'Unknown error')}")
                        
                else:
                    st.error(f"❌ API Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ **Connection Error:** Could not connect to the backend API. Make sure your Flask server is running.")
            except requests.exceptions.Timeout:
                st.error("❌ **Timeout:** The request took too long. This might happen if there are many tickets to process.")
            except Exception as e:
                st.error(f"❌ **Error:** {str(e)}")

# Footer with instructions (collapsible)
with st.expander("📚 How It Works", expanded=False):
    st.markdown("""
    ### How SubcontractorHub AI Agent Works:
    
    1. **Complete Database Search**: Searches through ALL tickets in your Critical Ops board (1000+ tickets)
    
    2. **Deep Context Analysis**: Analyzes 100% of ticket context including:
       - Ticket descriptions
       - All comments (showing resolution steps)
       - Status changes
       - Resolution details
    
    3. **Semantic Matching**: Uses AI-powered semantic search to find the most relevant tickets to your query
    
    4. **Consultant-Level Analysis**: Provides comprehensive, strategic insights similar to McKinsey consulting:
       - Executive Summary
       - Problem Analysis
       - Root Cause Analysis
       - Step-by-Step Resolution Methodology
       - Key Learnings & Best Practices
       - Risk Mitigation Recommendations
    
    5. **Smart Response**: 
       - If similar incidents found: Provides detailed resolution guide
       - If no similar incidents: Advises to contact POC for investigation
    
    ### Current Configuration:
    - **Project Filter**: CO (Critical Ops)
    - **Search Scope**: Entire database (all tickets)
    - **Backend URL**: http://localhost:5000
    - **AI Model**: Google Gemini 2.5 Flash
    """)
