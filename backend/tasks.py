from celery import shared_task
from services.jira_service import JiraService
from config import Config
import time
import logging
import json
from services.weaviate_service import WeaviateService
import google.generativeai as genai

logger = logging.getLogger(__name__)

@shared_task(name='tasks.test_task')
def test_task():
    time.sleep(5)  # Simulate some work
    return {'status': 'Task completed successfully'}

@shared_task(name='tasks.process_jira_webhook')
def process_jira_webhook(data):
    try:
        # Extract issue ID and project info from webhook data
        issue_id = data['issue']['id']
        project_name = data['issue'].get('fields', {}).get('project', {}).get('name', '')
        project_key = data['issue'].get('fields', {}).get('project', {}).get('key', '')
        
        # Filter: Only process tickets from "CO" project (Critical Ops board)
        target_project_key = Config.JIRA_PROJECT_KEY
        if project_key != target_project_key:
            logger.info(f"Skipping issue {issue_id} from project '{project_key}' (not '{target_project_key}')")
            return {
                'status': 'skipped',
                'message': f"Issue from project '{project_key}' skipped (only processing '{target_project_key}')"
            }
        
        logger.info(f"Processing issue {issue_id} from '{project_name}' board (project key: {project_key})")
        
        # Initialize Jira service
        jira_service = JiraService(
            Config.JIRA_URL,
            Config.JIRA_USERNAME,
            Config.JIRA_API_TOKEN
        )
        
        # Fetch complete issue details
        issue_details = jira_service.get_issue_details(issue_id)
        
        # Initialize Weaviate service and store data
        weaviate_service = WeaviateService()
        try:
            # Insert issue with embedded comments
            issue_uuid = weaviate_service.insert_issue(issue_details)
            
            logger.info(f"Successfully stored issue {issue_id} in Weaviate")
            return {
                'status': 'success',
                'message': f'Issue {issue_id} processed and stored',
                'issue_uuid': issue_uuid
            }
            
        finally:
            weaviate_service.close()
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task(name='tasks.process_user_query')
def process_user_query(query):
    try:
        weaviate_service = WeaviateService()
        
        system_prompt = """You are a senior McKinsey consultant analyzing Critical Ops support tickets. 
        Your role is to provide comprehensive, strategic, and actionable insights to account managers.
        
        CRITICAL INSTRUCTIONS - Write like a McKinsey consultant:
        1. Analyze EVERY detail with deep rigor - description, all comments, status changes, resolution steps, and underlying patterns
        2. Extract COMPLETE context - what occurred, why it happened, root causes, impact, and how it was solved
        3. Provide comprehensive, executive-level analysis with:
           - Executive Summary (2-3 sentences)
           - Detailed Problem Analysis (what happened, why, impact)
           - Root Cause Analysis (underlying issues)
           - Step-by-Step Resolution Guide (detailed, actionable steps)
           - Key Learnings & Best Practices
           - Risk Mitigation Recommendations
        4. Use professional consulting language: structured, clear, data-driven, strategic
        5. Only reference tickets that are ACTUALLY relevant to the user's query
        6. If NO tickets are relevant, clearly state: "No such incident has occurred before. Please reach out to the respective POC (Point of Contact) to investigate further."
        
        RESPONSE STRUCTURE (McKinsey-style):
        ============================================
        EXECUTIVE SUMMARY
        [2-3 sentence overview of the issue and resolution approach]
        
        PROBLEM ANALYSIS
        [Detailed description of what occurred, when, who was affected, business impact]
        
        ROOT CAUSE ANALYSIS
        [Deep dive into why this happened - technical, process, or systemic issues]
        
        RESOLUTION METHODOLOGY
        [Step-by-step guide based on actual ticket resolutions, with context for each step]
        
        KEY LEARNINGS & BEST PRACTICES
        [Patterns identified, preventive measures, recommendations]
        
        RISK MITIGATION & PREVENTION
        [How to avoid similar issues in the future]
        ============================================
        
        Be thorough, strategic, and provide actionable insights that demonstrate deep understanding."""

        try:
            collection = weaviate_service.client.collections.get("JiraIssue")

            # Filter queries to only search within "CO" project tickets (Critical Ops board)
            target_project_key = Config.JIRA_PROJECT_KEY
            from weaviate.classes.query import Filter
            
            # IMPORTANT: Weaviate hybrid search searches through ALL tickets in the database
            # It performs semantic search across every ticket, then returns the top N most relevant ones
            # The limit parameter only controls how many results to return, NOT how many to search
            # So this WILL search all 1400+ tickets if they're stored in Weaviate
            
            # Get total count of tickets in database for logging
            total_tickets_result = collection.query.fetch_objects(
                limit=10000,  # Large limit to count all tickets
                filters=Filter.by_property("project").equal(target_project_key)
            )
            total_tickets_in_db = len(total_tickets_result.objects)
            logger.info(f"Searching through {total_tickets_in_db} tickets in Weaviate database")
            
            # Hybrid search searches ALL tickets semantically, returns top matches
            # This searches every single ticket in the database, not just the limit
            response = collection.query.hybrid(
                query=query, 
                limit=30,  # Return top 30 most relevant tickets (but searches ALL tickets in database)
                filters=Filter.by_property("project").equal(target_project_key),
                alpha=0.75  # Weight towards semantic/vector search (0.75) vs keyword (0.25)
            )

            tickets = []
            ticket_keys = []
            
            for o in response.objects:
                ticket_data = o.properties
                tickets.append(ticket_data)
                ticket_keys.append(ticket_data.get('key', 'Unknown'))
            
            # Format tickets with COMPLETE context for deep analysis
            formatted_tickets = []
            for ticket in tickets:
                # Extract all comments chronologically to understand resolution steps
                comments_text = ""
                if ticket.get('comments'):
                    comments_text = "\n\nComments (in chronological order, showing resolution steps):\n"
                    for idx, comment in enumerate(ticket.get('comments', []), 1):
                        author = comment.get('author', 'Unknown')
                        body = comment.get('body', '')
                        created = comment.get('created', '')
                        comments_text += f"\n[{idx}] {author} ({created}):\n{body}\n"
                
                formatted_ticket = {
                    'ticket_key': ticket.get('key', 'N/A'),
                    'summary': ticket.get('summary', 'No summary'),
                    'description': ticket.get('description', 'No description'),
                    'status': ticket.get('status', 'N/A'),
                    'priority': ticket.get('priority', 'N/A'),
                    'labels': ticket.get('labels', []),
                    'assignee': ticket.get('assignee', 'Unassigned'),
                    'reporter': ticket.get('reporter', 'Unknown'),
                    'created_date': ticket.get('created', 'N/A'),
                    'resolution_date': ticket.get('resolutionDate', 'N/A'),
                    'all_comments': comments_text if comments_text else "No comments available",
                    'full_context': f"""
Ticket: {ticket.get('key', 'N/A')}
Summary: {ticket.get('summary', 'No summary')}
Description: {ticket.get('description', 'No description')}
Status: {ticket.get('status', 'N/A')}
Priority: {ticket.get('priority', 'N/A')}
{comments_text}
"""
                }
                formatted_tickets.append(formatted_ticket)

            # Build comprehensive context for the AI
            context = f"""USER QUERY: "{query}"

You are a McKinsey consultant analyzing Critical Ops support tickets to provide strategic, comprehensive guidance to account managers.

SEARCH RESULTS:
- Found {len(formatted_tickets)} tickets ranked by semantic relevance to the query
- Tickets are ordered from most relevant to least relevant
- Ticket keys analyzed: {', '.join(ticket_keys[:10])}{'...' if len(ticket_keys) > 10 else ''}

YOUR CONSULTING TASK:
1. Conduct deep analysis of each ticket's COMPLETE context (description + all comments + status changes)
2. Identify which tickets are ACTUALLY relevant to the user's query
3. Extract comprehensive resolution methodology from relevant tickets
4. Provide executive-level, strategic analysis following McKinsey consulting standards

CRITICAL REQUIREMENTS:
- Write like a senior consultant: professional, structured, comprehensive, strategic
- Provide DETAILED explanations - don't just list steps, explain WHY each step matters
- Include business context and impact analysis
- Extract root causes, not just symptoms
- Provide actionable recommendations with clear rationale
- If tickets are relevant: Provide comprehensive McKinsey-style analysis (see structure above)
- If NO tickets are relevant: State "No such incident has occurred before. Please reach out to the respective POC (Point of Contact) to investigate further."
- Base your response ONLY on the actual ticket data provided
- Be thorough - a consultant would never give a brief answer when detailed analysis is needed"""

            prompt = f"""{context}

TICKET DATA (Complete context for analysis):
{json.dumps(formatted_tickets, indent=2, default=str)}

CONSULTING ANALYSIS REQUIRED:
1. Review each ticket's full context (description + all comments + status changes) with deep analytical rigor
2. Determine relevance to query: "{query}" - be strategic about what's truly relevant
3. If relevant tickets exist:
   - Provide EXECUTIVE SUMMARY (2-3 sentences overview)
   - Conduct PROBLEM ANALYSIS (what occurred, when, impact, affected parties)
   - Perform ROOT CAUSE ANALYSIS (why it happened - technical, process, systemic issues)
   - Detail RESOLUTION METHODOLOGY (step-by-step guide with context and rationale for each step)
   - Extract KEY LEARNINGS & BEST PRACTICES (patterns, preventive measures)
   - Provide RISK MITIGATION & PREVENTION recommendations
   - Write in professional consulting style: structured, comprehensive, strategic
4. If NO relevant tickets exist:
   - Clearly state: "No such incident has occurred before. Please reach out to the respective POC (Point of Contact) to investigate further."

CONSULTING STANDARDS:
- Be comprehensive - a McKinsey consultant provides thorough analysis, not brief summaries
- Explain the "why" behind each resolution step, not just the "what"
- Include business impact and strategic implications
- Structure your response professionally with clear sections
- Use data-driven language and reference specific ticket details
- Provide actionable recommendations with clear rationale

Remember: Soak in 100% of the ticket context. Every comment may contain crucial resolution steps. Write as if presenting to a C-level executive."""

            # Configure Gemini API
            genai.configure(api_key=Config.GEMINI_API_KEY)
            
            # Use a more capable model for better analysis
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Create the full prompt with system instructions
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Generate response using Gemini API with longer context for comprehensive consultant-style analysis
            generation_config = {
                "temperature": 0.4,  # Slightly higher for more strategic, consultant-style thinking while staying factual
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,  # Increased for comprehensive McKinsey-style detailed responses
            }
            
            gemini_response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Extract the response text
            summary_text = gemini_response.text if gemini_response.text else "No summary provided"
            
            return {
                'status': 'success',
                'summary': summary_text,
                'tickets_found': len(tickets),
                'ticket_keys': ticket_keys,
                'timestamp': time.time()
            }

        except Exception as e:
            # Handle exceptions during processing
            logger.error(f"Error in query processing: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': f"An error occurred during processing: {str(e)}",
                'timestamp': time.time()
            }

        finally:
            weaviate_service.close()

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }