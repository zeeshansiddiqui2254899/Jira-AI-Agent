import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="JIRA AI Agent - Critical Ops",
    page_icon="🎫",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0052CC;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E3FCEF;
        border-left: 4px solid #36B37E;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #DEEBFF;
        border-left: 4px solid #0052CC;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🎫 JIRA AI Agent - Critical Ops</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ask questions about your support tickets and get AI-powered insights</div>', unsafe_allow_html=True)

# Sidebar for configuration
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
        status = "🟢 Online" if response.status_code in [200, 400] else "🔴 Offline"
    except:
        status = "🔴 Offline"
    
    st.markdown(f"**Backend:** {status}")
    
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. Type your question in the search box
    2. Click "Search Tickets"
    3. Get AI-powered insights from your Critical Ops tickets
    
    **Example Questions:**
    - "How do we handle login issues?"
    - "What are common payment problems?"
    - "Show me tickets about API errors"
    """)

# Main content area
st.markdown("### 🔍 Search Your Support Tickets")

# Query input
user_query = st.text_area(
    "Ask a question about your Critical Ops support tickets:",
    placeholder="Example: How do we typically resolve authentication errors?",
    height=100
)

col1, col2 = st.columns([1, 5])
with col1:
    search_button = st.button("🔎 Search Tickets", type="primary", use_container_width=True)

# Display results
if search_button:
    if not user_query.strip():
        st.warning("⚠️ Please enter a question to search.")
    else:
        with st.spinner("🔍 Searching through your tickets and generating insights..."):
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
                            st.warning("⚠️ No Similar Incidents Found")
                            st.markdown('<div class="info-box">', unsafe_allow_html=True)
                            st.markdown(summary)
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.success("✅ Found relevant tickets and generated step-by-step resolution guide!")
                            
                            # Display the summary with better formatting
                            st.markdown("### 📋 Resolution Guide")
                            st.markdown('<div class="success-box">', unsafe_allow_html=True)
                            
                            # Format the response for better readability
                            formatted_summary = summary
                            
                            # Add line breaks for better formatting
                            formatted_summary = formatted_summary.replace('\n\n', '\n\n')
                            
                            st.markdown(formatted_summary)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Show ticket references if available
                            ticket_keys = data.get('ticket_keys', [])
                            if ticket_keys:
                                st.markdown("---")
                                st.markdown("### 📎 Referenced Tickets")
                                ticket_list = ", ".join(ticket_keys[:10])
                                if len(ticket_keys) > 10:
                                    ticket_list += f" and {len(ticket_keys) - 10} more"
                                st.info(f"Based on analysis of tickets: **{ticket_list}**")
                        
                        # Additional info
                        st.markdown("---")
                        st.markdown("### ℹ️ About This Response")
                        st.info(
                            f"This response analyzes **100% of the ticket context** including descriptions, comments, and resolution steps "
                            f"from your **Critical Ops** board to provide accurate step-by-step resolution guides."
                        )
                    else:
                        st.error(f"❌ Error: {data.get('message', 'Unknown error')}")
                        
                else:
                    st.error(f"❌ API Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ **Connection Error:** Could not connect to the backend API. Make sure your Flask server is running on the configured URL.")
                st.info("💡 **Tip:** Check if the backend is running by looking at the status in the sidebar.")
            except requests.exceptions.Timeout:
                st.error("❌ **Timeout:** The request took too long. This might happen if there are many tickets to process.")
            except Exception as e:
                st.error(f"❌ **Error:** {str(e)}")

# Footer with instructions
st.markdown("---")
with st.expander("📚 How It Works"):
    st.markdown("""
    ### How the JIRA AI Agent Works:
    
    1. **Complete Database Search**: Searches through ALL tickets in your Critical Ops board (1400+ tickets)
    
    2. **Deep Context Analysis**: Analyzes 100% of ticket context including:
       - Ticket descriptions
       - All comments (showing resolution steps)
       - Status changes
       - Resolution details
    
    3. **Semantic Matching**: Uses AI-powered semantic search to find the most relevant tickets to your query
    
    4. **Step-by-Step Solutions**: Extracts complete resolution guides from similar past incidents
    
    5. **Smart Response**: 
       - If similar incidents found: Provides detailed step-by-step resolution guide
       - If no similar incidents: Advises to contact POC for investigation
    
    ### Current Configuration:
    - **Project Filter**: CO (Critical Ops)
    - **Search Scope**: Entire database (all tickets)
    - **Backend URL**: http://localhost:5000
    - **AI Model**: Google Gemini 2.5 Flash
    """)

with st.expander("🔧 Troubleshooting"):
    st.markdown("""
    ### Common Issues:
    
    **"Connection Error"**
    - Make sure the Flask backend is running
    - Check the API URL in the sidebar
    - Verify services: `ps aux | grep -E "(celery|gunicorn)"`
    
    **"No results found"**
    - Make sure you have closed tickets in the CO project
    - Check if webhooks are configured correctly
    - Verify tickets are being stored: Check Celery logs
    
    **"Timeout Error"**
    - The AI is processing many tickets
    - Wait a bit longer or try a more specific question
    """)

