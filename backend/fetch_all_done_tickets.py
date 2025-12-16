#!/usr/bin/env python3
"""
Fetch all "Done" tickets from CO project (since they use "Done" instead of "Closed")
"""

from config import Config
from services.jira_service import JiraService
from services.weaviate_service import WeaviateService
import requests
from requests.auth import HTTPBasicAuth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_and_fetch_done_tickets():
    """Find all Done tickets by checking ticket numbers"""
    print("=" * 70)
    print("📥 FETCHING ALL DONE TICKETS - Critical Ops (CO Project)")
    print("=" * 70)
    print()
    
    auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
    headers = {'Accept': 'application/json'}
    
    print("🔍 Scanning for Done tickets in CO project...")
    print("   (This may take a minute - checking ticket numbers...)")
    print()
    
    done_ticket_keys = []
    checked = 0
    
    # Check a wide range of ticket numbers
    for i in range(1, 500):
        ticket_key = f'CO-{i}'
        checked += 1
        if checked % 50 == 0:
            print(f"   Checked {checked} tickets, found {len(done_ticket_keys)} Done tickets so far...")
        
        try:
            url = f'{Config.JIRA_URL}/rest/api/3/issue/{ticket_key}'
            response = requests.get(url, headers=headers, auth=auth, timeout=2)
            
            if response.status_code == 200:
                issue = response.json()
                project = issue.get('fields', {}).get('project', {}).get('key', '')
                status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
                
                if project == 'CO' and status == 'Done':
                    done_ticket_keys.append(ticket_key)
        except:
            continue
    
    print()
    print(f"✅ Found {len(done_ticket_keys)} Done tickets")
    print()
    
    if len(done_ticket_keys) == 0:
        print("⚠️  No Done tickets found.")
        print("   Make sure you have completed tickets in your Critical Ops board.")
        return
    
    # Show sample
    print("Sample tickets found:")
    for key in done_ticket_keys[:10]:
        print(f"   - {key}")
    if len(done_ticket_keys) > 10:
        print(f"   ... and {len(done_ticket_keys) - 10} more")
    print()
    
    # Ask for confirmation
    print("=" * 70)
    print(f"Ready to fetch and store {len(done_ticket_keys)} tickets")
    print("=" * 70)
    print()
    
    # Initialize services
    jira_service = JiraService(
        Config.JIRA_URL,
        Config.JIRA_USERNAME,
        Config.JIRA_API_TOKEN
    )
    weaviate_service = WeaviateService()
    
    success_count = 0
    error_count = 0
    
    print("💾 Storing tickets in database...")
    print()
    
    for i, ticket_key in enumerate(done_ticket_keys, 1):
        print(f"[{i}/{len(done_ticket_keys)}] Processing {ticket_key}...", end=" ")
        
        try:
            # Get issue by key first to get the ID
            url = f'{Config.JIRA_URL}/rest/api/3/issue/{ticket_key}'
            response = requests.get(url, headers=headers, auth=auth)
            
            if response.status_code != 200:
                print(f"❌ Not found")
                error_count += 1
                continue
            
            issue_data = response.json()
            issue_id = issue_data.get('id')
            
            # Fetch full details
            issue_details = jira_service.get_issue_details(issue_id)
            
            # Store in Weaviate
            issue_uuid = weaviate_service.insert_issue(issue_details)
            
            summary = issue_data.get('fields', {}).get('summary', 'N/A')[:45]
            print(f"✅ Stored - {summary}...")
            success_count += 1
            
        except Exception as e:
            error_msg = str(e)[:40]
            print(f"❌ Error: {error_msg}")
            error_count += 1
            logger.error(f"Error processing {ticket_key}: {str(e)}")
    
    print()
    print("=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully stored: {success_count} tickets")
    if error_count > 0:
        print(f"❌ Errors: {error_count} tickets")
    print()
    print(f"🎉 Database now contains {success_count} tickets!")
    print()
    print("You can now:")
    print("   🌐 Query tickets: http://localhost:8501")
    print("   🔌 Use API: POST http://localhost:5000/api/query")
    print("=" * 70)
    
    weaviate_service.close()

if __name__ == "__main__":
    find_and_fetch_done_tickets()

