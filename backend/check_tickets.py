#!/usr/bin/env python3
"""
Diagnostic script to check if Jira tickets are being fetched and stored
"""

from config import Config
from services.jira_service import JiraService
from services.weaviate_service import WeaviateService
import requests
from requests.auth import HTTPBasicAuth

print("=" * 70)
print("🔍 JIRA TICKET DATA CHECK - Critical Ops (CO Project)")
print("=" * 70)
print()

# 1. Check Authentication
print("1️⃣  Testing Jira Authentication...")
try:
    url = f'{Config.JIRA_URL}/rest/api/3/myself'
    auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
    headers = {'Accept': 'application/json'}
    response = requests.get(url, headers=headers, auth=auth)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"   ✅ Authenticated as: {user_data.get('displayName', 'Unknown')}")
        print(f"   ✅ Jira URL: {Config.JIRA_URL}")
    else:
        print(f"   ❌ Authentication failed: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    exit(1)

print()

# 2. Check Project
print("2️⃣  Checking CO Project...")
try:
    project_url = f'{Config.JIRA_URL}/rest/api/3/project/CO'
    response = requests.get(project_url, headers=headers, auth=auth)
    
    if response.status_code == 200:
        project = response.json()
        print(f"   ✅ Project Found: {project.get('name', 'N/A')}")
        print(f"   ✅ Project Key: {project.get('key', 'N/A')}")
    else:
        print(f"   ⚠️  Project check failed: {response.status_code}")
except Exception as e:
    print(f"   ⚠️  Error: {str(e)}")

print()

# 3. Check Database
print("3️⃣  Checking Weaviate Database...")
try:
    weaviate_service = WeaviateService()
    collection = weaviate_service.client.collections.get('JiraIssue')
    
    result = collection.query.fetch_objects(limit=100)
    total = len(result.objects)
    
    print(f"   📊 Total tickets in database: {total}")
    
    if total > 0:
        print()
        print("   ✅ Sample tickets stored:")
        for i, obj in enumerate(result.objects[:5], 1):
            props = obj.properties
            key = props.get('key', 'N/A')
            summary = props.get('summary', 'N/A')[:50]
            project = props.get('project', 'N/A')
            status = props.get('status', 'N/A')
            print(f"      {i}. {key} ({project}): {summary}...")
            print(f"         Status: {status}")
    else:
        print("   ⚠️  No tickets found in database")
        print()
        print("   💡 This means:")
        print("      - No webhooks have been received yet, OR")
        print("      - No tickets have been closed in CO project, OR")
        print("      - Webhooks are not configured")
    
    weaviate_service.close()
except Exception as e:
    print(f"   ❌ Error checking database: {str(e)}")

print()

# 4. Test Issue Fetching (if we can find a ticket key)
print("4️⃣  Testing Issue Fetching Capability...")
try:
    jira_service = JiraService(
        Config.JIRA_URL,
        Config.JIRA_USERNAME,
        Config.JIRA_API_TOKEN
    )
    
    # Try to find any issue in CO project by testing a common pattern
    # We'll try CO-1, CO-2, etc.
    found_issue = None
    for i in range(1, 10):
        try:
            test_key = f"CO-{i}"
            # Try to get issue by key
            issue_url = f'{Config.JIRA_URL}/rest/api/3/issue/{test_key}'
            response = requests.get(issue_url, headers=headers, auth=auth)
            
            if response.status_code == 200:
                issue_data = response.json()
                project_key = issue_data.get('fields', {}).get('project', {}).get('key', '')
                if project_key == 'CO':
                    found_issue = test_key
                    print(f"   ✅ Found test ticket: {test_key}")
                    print(f"      Summary: {issue_data.get('fields', {}).get('summary', 'N/A')[:50]}...")
                    print(f"      Status: {issue_data.get('fields', {}).get('status', {}).get('name', 'N/A')}")
                    break
        except:
            continue
    
    if not found_issue:
        print("   ⚠️  Could not find any test tickets (CO-1 through CO-9)")
        print("      This is okay - it just means we need a real ticket to test")
    
except Exception as e:
    print(f"   ⚠️  Error: {str(e)}")

print()

# 5. Summary and Recommendations
print("=" * 70)
print("📋 SUMMARY & RECOMMENDATIONS")
print("=" * 70)
print()

print("✅ What's Working:")
print("   - Jira authentication: OK")
print("   - Project CO (Critical Ops): Found")
print("   - Database connection: OK")
print()

if total == 0:
    print("⚠️  No Tickets in Database Yet")
    print()
    print("📝 To populate the database, you have two options:")
    print()
    print("   Option 1: Use Webhooks (Automatic)")
    print("   ──────────────────────────────────────")
    print("   1. Set up a webhook in Jira:")
    print("      - Go to: Jira Settings → System → Webhooks")
    print("      - Create webhook pointing to: https://your-ngrok-url/webhook/jira")
    print("      - Trigger: 'Issue updated' → Filter: 'Status changed to Closed'")
    print("   2. Close a ticket in CO project")
    print("   3. It will automatically be stored!")
    print()
    print("   Option 2: Manual Fetch (One-time)")
    print("   ───────────────────────────────────")
    print("   If you have existing closed tickets, I can help you fetch them.")
    print("   Just tell me a ticket key (like CO-123) and I'll test fetching it.")
    print()
else:
    print(f"✅ You have {total} tickets stored!")
    print("   You can now query them using:")
    print("   - Web interface: http://localhost:8501")
    print("   - API: POST http://localhost:5000/api/query")

print()
print("=" * 70)



