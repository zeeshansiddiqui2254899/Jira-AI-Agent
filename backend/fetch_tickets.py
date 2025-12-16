#!/usr/bin/env python3
"""
Script to manually fetch and store Jira tickets from CO project
This helps populate the database with existing closed tickets
"""

from config import Config
from services.jira_service import JiraService
from services.weaviate_service import WeaviateService
import requests
from requests.auth import HTTPBasicAuth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_closed_tickets(project_key='CO', max_results=50):
    """Fetch closed tickets from Jira"""
    # Use POST method with JQL endpoint
    url = f'{Config.JIRA_URL}/rest/api/3/search'
    auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    
    jql = f'project = {project_key} AND status = Closed ORDER BY updated DESC'
    payload = {
        'jql': jql,
        'maxResults': max_results,
        'fields': ['summary', 'status', 'project', 'key', 'description', 'comment', 'priority', 'labels', 'assignee', 'reporter', 'created', 'updated', 'resolutiondate', 'attachment']
    }
    
    logger.info(f"Fetching closed tickets from project {project_key}...")
    response = requests.post(url, headers=headers, auth=auth, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        issues = data.get('issues', [])
        logger.info(f"Found {total} closed tickets, fetching details for {len(issues)} tickets...")
        return issues
    else:
        logger.error(f"Error fetching tickets: {response.status_code} - {response.text}")
        return []

def main():
    print("=" * 60)
    print("JIRA Ticket Fetcher - Critical Ops (CO Project)")
    print("=" * 60)
    print()
    
    # Initialize services
    jira_service = JiraService(
        Config.JIRA_URL,
        Config.JIRA_USERNAME,
        Config.JIRA_API_TOKEN
    )
    
    weaviate_service = WeaviateService()
    
    try:
        # Fetch closed tickets
        tickets = fetch_closed_tickets(project_key=Config.JIRA_PROJECT_KEY, max_results=50)
        
        if not tickets:
            print("⚠️  No closed tickets found in CO project.")
            print("   Make sure you have closed tickets in your Critical Ops board.")
            return
        
        print(f"\n📥 Found {len(tickets)} closed tickets to process")
        print()
        
        # Process each ticket
        success_count = 0
        error_count = 0
        
        for i, ticket_summary in enumerate(tickets, 1):
            issue_id = ticket_summary['id']
            issue_key = ticket_summary['key']
            
            print(f"[{i}/{len(tickets)}] Processing {issue_key}...", end=" ")
            
            try:
                # Fetch full ticket details
                issue_details = jira_service.get_issue_details(issue_id)
                
                # Store in Weaviate
                issue_uuid = weaviate_service.insert_issue(issue_details)
                
                print(f"✅ Stored")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
                error_count += 1
                logger.error(f"Error processing {issue_key}: {str(e)}")
        
        print()
        print("=" * 60)
        print(f"✅ Successfully stored: {success_count} tickets")
        if error_count > 0:
            print(f"❌ Errors: {error_count} tickets")
        print("=" * 60)
        print()
        print("🎉 Done! You can now query these tickets using the web interface.")
        print("   Open: http://localhost:8501")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        weaviate_service.close()

if __name__ == "__main__":
    main()

