#!/usr/bin/env python3
"""
RCA Script: Check if Weaviate has all Jira ticket data
Compares tickets in Weaviate vs tickets in Jira CO project
"""

from config import Config
from services.weaviate_service import WeaviateService
from services.jira_service import JiraService
import requests
from requests.auth import HTTPBasicAuth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_weaviate_tickets():
    """Get all tickets stored in Weaviate"""
    print("=" * 70)
    print("📊 CHECKING WEAVIATE DATA")
    print("=" * 70)
    print()
    
    weaviate_service = WeaviateService()
    
    try:
        collection = weaviate_service.client.collections.get("JiraIssue")
        
        # Get all tickets from CO project
        from weaviate.classes.query import Filter
        response = collection.query.fetch_objects(
            limit=10000,  # Large limit to get all tickets
            filters=Filter.by_property("project").equal(Config.JIRA_PROJECT_KEY)
        )
        
        tickets = []
        for obj in response.objects:
            tickets.append({
                'key': obj.properties.get('key'),
                'issueID': obj.properties.get('issueID'),
                'summary': obj.properties.get('summary'),
                'status': obj.properties.get('status'),
                'created': obj.properties.get('created')
            })
        
        print(f"✅ Found {len(tickets)} tickets in Weaviate (CO project)")
        print()
        
        # Show sample tickets
        if tickets:
            print("📋 Sample tickets in Weaviate:")
            for i, ticket in enumerate(tickets[:10], 1):
                print(f"   {i}. {ticket['key']} - {ticket['summary'][:50] if ticket['summary'] else 'No summary'}... [{ticket['status']}]")
            if len(tickets) > 10:
                print(f"   ... and {len(tickets) - 10} more")
        
        return tickets
        
    except Exception as e:
        logger.error(f"Error querying Weaviate: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return []
    finally:
        weaviate_service.close()

def get_jira_tickets():
    """Get all tickets from Jira CO project"""
    print()
    print("=" * 70)
    print("📊 CHECKING JIRA DATA")
    print("=" * 70)
    print()
    
    auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    
    all_tickets = []
    start_at = 0
    max_results = 100
    
    print(f"🔍 Fetching tickets from Jira CO project...")
    
    while True:
        url = f'{Config.JIRA_URL}/rest/api/3/search'
        payload = {
            'jql': f'project = {Config.JIRA_PROJECT_KEY} ORDER BY created ASC',
            'startAt': start_at,
            'maxResults': max_results,
            'fields': ['key', 'id', 'summary', 'status', 'created']
        }
        
        try:
            response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get('issues', [])
                total = data.get('total', 0)
                
                if start_at == 0:
                    print(f"   Total tickets in Jira: {total}")
                    print()
                
                for issue in issues:
                    all_tickets.append({
                        'key': issue.get('key'),
                        'id': issue.get('id'),
                        'summary': issue.get('fields', {}).get('summary'),
                        'status': issue.get('fields', {}).get('status', {}).get('name'),
                        'created': issue.get('fields', {}).get('created')
                    })
                
                print(f"   📦 Fetched batch: {start_at + 1} to {start_at + len(issues)} tickets")
                
                if len(issues) < max_results or start_at + len(issues) >= total:
                    break
                
                start_at += max_results
                
            elif response.status_code == 410:
                print(f"⚠️  API endpoint returned 410 Gone (deprecated)")
                print(f"   Trying alternative method...")
                # Fallback: try individual ticket fetching
                return get_jira_tickets_fallback()
            else:
                print(f"❌ Error fetching tickets: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                break
                
        except Exception as e:
            logger.error(f"Error fetching Jira tickets: {str(e)}")
            print(f"❌ Error: {str(e)}")
            break
    
    print()
    print(f"✅ Found {len(all_tickets)} tickets in Jira")
    print()
    
    # Show sample tickets
    if all_tickets:
        print("📋 Sample tickets in Jira:")
        for i, ticket in enumerate(all_tickets[:10], 1):
            summary = ticket['summary'][:50] if ticket['summary'] else 'No summary'
            print(f"   {i}. {ticket['key']} - {summary}... [{ticket['status']}]")
        if len(all_tickets) > 10:
            print(f"   ... and {len(all_tickets) - 10} more")
    
    return all_tickets

def get_jira_tickets_fallback():
    """Fallback method: Try to estimate ticket count by checking ticket numbers"""
    print("   Using fallback method: Checking ticket number ranges...")
    
    auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
    headers = {'Accept': 'application/json'}
    
    found_tickets = []
    checked = 0
    
    # Check ticket numbers from 1 to 1000
    for i in range(1, 1001):
        ticket_key = f'{Config.JIRA_PROJECT_KEY}-{i}'
        checked += 1
        
        if checked % 100 == 0:
            print(f"   Checked {checked} ticket numbers, found {len(found_tickets)} so far...")
        
        try:
            url = f'{Config.JIRA_URL}/rest/api/3/issue/{ticket_key}'
            response = requests.get(url, headers=headers, auth=auth, timeout=2)
            
            if response.status_code == 200:
                issue = response.json()
                project_key = issue.get('fields', {}).get('project', {}).get('key', '')
                
                if project_key == Config.JIRA_PROJECT_KEY:
                    found_tickets.append({
                        'key': issue.get('key'),
                        'id': issue.get('id'),
                        'summary': issue.get('fields', {}).get('summary'),
                        'status': issue.get('fields', {}).get('status', {}).get('name'),
                        'created': issue.get('fields', {}).get('created')
                    })
        except:
            continue
    
    print(f"   ✅ Found {len(found_tickets)} tickets using fallback method")
    return found_tickets

def compare_data(weaviate_tickets, jira_tickets):
    """Compare tickets in Weaviate vs Jira"""
    print()
    print("=" * 70)
    print("🔍 COMPARISON ANALYSIS")
    print("=" * 70)
    print()
    
    # Create sets of ticket keys
    weaviate_keys = {t['key'] for t in weaviate_tickets}
    jira_keys = {t['key'] for t in jira_tickets}
    
    print(f"📊 Statistics:")
    print(f"   • Tickets in Weaviate: {len(weaviate_tickets)}")
    print(f"   • Tickets in Jira: {len(jira_tickets)}")
    print()
    
    # Find missing tickets
    missing_in_weaviate = jira_keys - weaviate_keys
    extra_in_weaviate = weaviate_keys - jira_keys
    
    print(f"🔍 Analysis Results:")
    print()
    
    if len(missing_in_weaviate) == 0 and len(extra_in_weaviate) == 0:
        print("   ✅ PERFECT MATCH!")
        print("   All Jira tickets are stored in Weaviate.")
    else:
        if missing_in_weaviate:
            print(f"   ⚠️  Missing in Weaviate: {len(missing_in_weaviate)} tickets")
            print(f"      These tickets exist in Jira but are NOT in Weaviate:")
            missing_list = sorted(list(missing_in_weaviate))[:20]
            for key in missing_list:
                ticket = next((t for t in jira_tickets if t['key'] == key), None)
                status = ticket['status'] if ticket else 'Unknown'
                print(f"      • {key} [{status}]")
            if len(missing_in_weaviate) > 20:
                print(f"      ... and {len(missing_in_weaviate) - 20} more")
            print()
        
        if extra_in_weaviate:
            print(f"   ℹ️  Extra in Weaviate: {len(extra_in_weaviate)} tickets")
            print(f"      These tickets are in Weaviate but NOT in Jira (may have been deleted):")
            extra_list = sorted(list(extra_in_weaviate))[:10]
            for key in extra_list:
                print(f"      • {key}")
            if len(extra_in_weaviate) > 10:
                print(f"      ... and {len(extra_in_weaviate) - 10} more")
            print()
    
    # Status breakdown
    print(f"📈 Status Breakdown in Jira:")
    status_counts = {}
    for ticket in jira_tickets:
        status = ticket['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        print(f"   • {status}: {count} tickets")
    
    print()
    print(f"📈 Status Breakdown in Weaviate:")
    weaviate_status_counts = {}
    for ticket in weaviate_tickets:
        status = ticket['status']
        weaviate_status_counts[status] = weaviate_status_counts.get(status, 0) + 1
    
    for status, count in sorted(weaviate_status_counts.items()):
        print(f"   • {status}: {count} tickets")
    
    return {
        'weaviate_count': len(weaviate_tickets),
        'jira_count': len(jira_tickets),
        'missing': list(missing_in_weaviate),
        'extra': list(extra_in_weaviate)
    }

def main():
    print()
    print("🔍 ROOT CAUSE ANALYSIS: Weaviate vs Jira Data Comparison")
    print()
    
    # Get tickets from Weaviate
    weaviate_tickets = get_weaviate_tickets()
    
    # Get tickets from Jira
    jira_tickets = get_jira_tickets()
    
    if not jira_tickets:
        print("⚠️  Could not fetch tickets from Jira. Please check your Jira connection.")
        return
    
    # Compare
    comparison = compare_data(weaviate_tickets, jira_tickets)
    
    print()
    print("=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print()
    
    if comparison['missing']:
        print(f"⚠️  ACTION REQUIRED:")
        print(f"   {len(comparison['missing'])} tickets need to be imported from Jira to Weaviate")
        print()
        print("   To import missing tickets, run:")
        print("   python3 backend/import_missing_tickets.py")
    else:
        print("✅ All tickets are synchronized!")
        print("   Weaviate contains all tickets from the Jira CO project.")
    
    print()

if __name__ == "__main__":
    main()



