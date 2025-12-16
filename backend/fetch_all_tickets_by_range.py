#!/usr/bin/env python3
"""
Fetch ALL tickets from CO project by checking ticket keys sequentially
This works around API limitations by fetching tickets individually
"""

from config import Config
from services.jira_service import JiraService
from services.weaviate_service import WeaviateService
import requests
from requests.auth import HTTPBasicAuth
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_existing_ticket_keys():
    """Get all ticket keys already in Weaviate to avoid duplicates"""
    weaviate_service = WeaviateService()
    try:
        collection = weaviate_service.client.collections.get("JiraIssue")
        from weaviate.classes.query import Filter
        
        result = collection.query.fetch_objects(
            limit=10000,
            filters=Filter.by_property("project").equal(Config.JIRA_PROJECT_KEY)
        )
        
        existing_keys = set()
        for obj in result.objects:
            key = obj.properties.get('key')
            if key:
                existing_keys.add(key)
        
        return existing_keys
    finally:
        weaviate_service.close()

def fetch_all_tickets_by_range():
    """Fetch all tickets by checking ticket keys sequentially"""
    print("=" * 70)
    print("📥 FETCHING ALL TICKETS BY KEY RANGE - Critical Ops (CO Project)")
    print("=" * 70)
    print()
    
    # First, check what tickets already exist in Weaviate
    print("🔍 Checking existing tickets in Weaviate...")
    existing_keys = get_existing_ticket_keys()
    print(f"   Found {len(existing_keys)} tickets already in database")
    print()
    
    auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
    headers = {'Accept': 'application/json'}
    
    print("🔍 Scanning for tickets in CO project...")
    print("   (Checking ticket keys CO-1 through CO-2000)")
    print()
    
    found_tickets = []
    checked = 0
    not_found_count = 0
    consecutive_not_found = 0
    
    # Check a wide range - adjust max_range if you have more than 2000 tickets
    max_range = 2000
    
    for i in range(1, max_range + 1):
        ticket_key = f'CO-{i}'
        checked += 1
        
        if checked % 100 == 0:
            print(f"   Checked {checked} tickets, found {len(found_tickets)} so far...")
        
        try:
            url = f'{Config.JIRA_URL}/rest/api/3/issue/{ticket_key}'
            response = requests.get(url, headers=headers, auth=auth, timeout=5)
            
            if response.status_code == 200:
                issue = response.json()
                project_key = issue.get('fields', {}).get('project', {}).get('key', '')
                
                if project_key == Config.JIRA_PROJECT_KEY:
                    # Store the full issue data, not just summary
                    found_tickets.append({
                        'key': ticket_key,
                        'id': issue.get('id'),
                        'summary': issue.get('fields', {}).get('summary', ''),
                        'status': issue.get('fields', {}).get('status', {}).get('name', 'N/A'),
                        'full_issue_data': issue  # Store full data to avoid re-fetching
                    })
                    consecutive_not_found = 0
                else:
                    consecutive_not_found += 1
            elif response.status_code == 404:
                consecutive_not_found += 1
                not_found_count += 1
            else:
                # Rate limiting or other error - wait a bit
                if response.status_code == 429:
                    print(f"   ⚠️  Rate limited, waiting 2 seconds...")
                    time.sleep(2)
                    continue
                consecutive_not_found += 1
                
        except requests.exceptions.Timeout:
            consecutive_not_found += 1
            continue
        except Exception as e:
            consecutive_not_found += 1
            continue
        
        # If we've had 50 consecutive not-found tickets, we might be past the end
        # But continue checking in case there are gaps
        if consecutive_not_found > 50 and len(found_tickets) > 0:
            # Check a bit more to be sure
            if consecutive_not_found > 100:
                print(f"   Stopping after {consecutive_not_found} consecutive not-found tickets")
                break
        
        # Small delay to avoid rate limiting
        if checked % 10 == 0:
            time.sleep(0.1)
    
    print()
    print(f"✅ Found {len(found_tickets)} tickets in Jira")
    print()
    
    if len(found_tickets) == 0:
        print("⚠️  No tickets found.")
        return
    
    # Filter out tickets that already exist
    new_tickets = []
    for ticket in found_tickets:
        key = ticket['key']
        if key not in existing_keys:
            new_tickets.append(ticket)
    
    print(f"📋 Summary:")
    print(f"   - Total tickets found: {len(found_tickets)}")
    print(f"   - Already in Weaviate: {len(found_tickets) - len(new_tickets)}")
    print(f"   - New tickets to import: {len(new_tickets)}")
    print()
    
    if len(new_tickets) == 0:
        print("✅ All tickets are already in Weaviate!")
        return
    
    # Show sample of tickets to import
    print("📝 Sample tickets to import:")
    for ticket in new_tickets[:10]:
        print(f"   - {ticket['key']}: {ticket['summary'][:50]}... [{ticket['status']}]")
    if len(new_tickets) > 10:
        print(f"   ... and {len(new_tickets) - 10} more")
    print()
    
    print("=" * 70)
    print(f"Ready to import {len(new_tickets)} tickets")
    print("=" * 70)
    print()
    
    # Initialize services
    print("💾 Initializing services...")
    jira_service = JiraService(
        Config.JIRA_URL,
        Config.JIRA_USERNAME,
        Config.JIRA_API_TOKEN
    )
    weaviate_service = WeaviateService()
    print("   ✅ Ready")
    print()
    
    print("=" * 70)
    print("📝 PROCESSING AND STORING TICKETS")
    print("=" * 70)
    print()
    
    # Process each ticket
    success_count = 0
    error_count = 0
    
    for i, ticket in enumerate(new_tickets, 1):
        issue_key = ticket['key']
        issue_id = ticket['id']
        status = ticket['status']
        
        print(f"[{i}/{len(new_tickets)}] Processing {issue_key} [{status}]...", end=" ")
        
        try:
            # Use the full issue data we already fetched, or fetch it if not available
            if 'full_issue_data' in ticket:
                issue_details = ticket['full_issue_data']
            else:
                # Fallback: fetch full ticket details using the issue ID
                issue_details = jira_service.get_issue_details(issue_id)
            
            # Validate issue_details is not None and has required structure
            if not issue_details:
                print(f"❌ Error: No data returned for {issue_key}")
                error_count += 1
                continue
            
            if 'fields' not in issue_details:
                print(f"❌ Error: Invalid data structure for {issue_key}")
                error_count += 1
                continue
            
            # Store in Weaviate
            issue_uuid = weaviate_service.insert_issue(issue_details)
            
            summary = ticket['summary'][:45] if ticket['summary'] else "No summary"
            print(f"✅ Stored - {summary}...")
            success_count += 1
            
            # Small delay every 10 tickets to avoid overwhelming the API
            if i % 10 == 0:
                time.sleep(0.3)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⏭️  Not found")
                # Don't count 404 as error - ticket might not exist
            else:
                error_msg = str(e)[:50]
                print(f"❌ HTTP Error: {error_msg}")
                error_count += 1
                logger.error(f"HTTP Error processing {issue_key}: {str(e)}")
        except Exception as e:
            error_msg = str(e)[:50]
            print(f"❌ Error: {error_msg}")
            error_count += 1
            logger.error(f"Error processing {issue_key}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    print()
    print("=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print()
    print(f"✅ Successfully stored: {success_count} tickets")
    if error_count > 0:
        print(f"❌ Errors: {error_count} tickets")
    print()
    
    # Get final count
    final_count = len(get_existing_ticket_keys())
    print(f"📈 Database now contains: {final_count} tickets from Critical Ops")
    print()
    print("🎉 Done! You can now:")
    print("   - Query tickets at: http://localhost:8501")
    print("   - Use the API: POST http://localhost:5000/api/query")
    print("=" * 70)
    
    weaviate_service.close()

if __name__ == "__main__":
    fetch_all_tickets_by_range()


