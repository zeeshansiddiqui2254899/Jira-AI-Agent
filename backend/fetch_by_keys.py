#!/usr/bin/env python3
"""
Fetch specific tickets by their keys (useful when search API is deprecated)
Usage: python3 fetch_by_keys.py CO-123 CO-456 CO-789
"""

import sys
from config import Config
from services.jira_service import JiraService
from services.weaviate_service import WeaviateService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_tickets_by_keys(ticket_keys):
    """Fetch and store specific tickets by their keys"""
    print("=" * 70)
    print("📥 FETCHING TICKETS BY KEY - Critical Ops (CO Project)")
    print("=" * 70)
    print()
    
    if not ticket_keys:
        print("⚠️  No ticket keys provided!")
        print()
        print("Usage:")
        print("  python3 fetch_by_keys.py CO-123 CO-456 CO-789")
        print()
        print("Or provide keys interactively:")
        print("  python3 fetch_by_keys.py")
        print("  Then enter ticket keys when prompted (one per line, empty to finish)")
        return
    
    # Initialize services
    jira_service = JiraService(
        Config.JIRA_URL,
        Config.JIRA_USERNAME,
        Config.JIRA_API_TOKEN
    )
    weaviate_service = WeaviateService()
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    print(f"📋 Processing {len(ticket_keys)} ticket(s)...")
    print()
    
    for i, ticket_key in enumerate(ticket_keys, 1):
        print(f"[{i}/{len(ticket_keys)}] Processing {ticket_key}...", end=" ")
        
        try:
            # Fetch ticket by key
            issue_url = f'{Config.JIRA_URL}/rest/api/3/issue/{ticket_key}'
            import requests
            from requests.auth import HTTPBasicAuth
            
            auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
            headers = {'Accept': 'application/json'}
            
            response = requests.get(issue_url, headers=headers, auth=auth)
            
            if response.status_code != 200:
                print(f"❌ Not found (Status: {response.status_code})")
                error_count += 1
                continue
            
            issue_data = response.json()
            project_key = issue_data.get('fields', {}).get('project', {}).get('key', '')
            
            # Check if it's from CO project
            if project_key != 'CO':
                print(f"⏭️  Skipped (project: {project_key}, not CO)")
                skipped_count += 1
                continue
            
            # Get issue ID and fetch full details
            issue_id = issue_data.get('id')
            issue_details = jira_service.get_issue_details(issue_id)
            
            # Store in Weaviate
            issue_uuid = weaviate_service.insert_issue(issue_details)
            
            summary = issue_data.get('fields', {}).get('summary', 'N/A')[:50]
            status = issue_data.get('fields', {}).get('status', {}).get('name', 'N/A')
            print(f"✅ Stored - {summary}... (Status: {status})")
            success_count += 1
            
        except Exception as e:
            error_msg = str(e)[:50]
            print(f"❌ Error: {error_msg}")
            error_count += 1
            logger.error(f"Error processing {ticket_key}: {str(e)}")
    
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully stored: {success_count} tickets")
    if skipped_count > 0:
        print(f"⏭️  Skipped (wrong project): {skipped_count} tickets")
    if error_count > 0:
        print(f"❌ Errors: {error_count} tickets")
    print()
    
    if success_count > 0:
        print("🎉 Done! Tickets are now available for querying.")
        print("   - Web interface: http://localhost:8501")
        print("   - API: POST http://localhost:5000/api/query")
    
    weaviate_service.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Get keys from command line arguments
        ticket_keys = [key.strip() for key in sys.argv[1:] if key.strip()]
    else:
        # Interactive mode
        print("Enter ticket keys (one per line, empty line to finish):")
        ticket_keys = []
        while True:
            key = input("Ticket key (e.g., CO-123): ").strip()
            if not key:
                break
            ticket_keys.append(key)
    
    fetch_tickets_by_keys(ticket_keys)



