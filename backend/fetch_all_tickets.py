#!/usr/bin/env python3
"""
Fetch ALL tickets from CO project (Critical Ops) and store them in Weaviate
This script handles pagination to fetch 1400+ tickets efficiently
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

def fetch_all_tickets_from_jira():
    """Fetch all tickets from CO project using Jira Python library with pagination"""
    print("=" * 70)
    print("📥 FETCHING ALL TICKETS - Critical Ops (CO Project)")
    print("=" * 70)
    print()
    
    # First, check what tickets already exist in Weaviate
    print("🔍 Checking existing tickets in Weaviate...")
    existing_keys = get_existing_ticket_keys()
    print(f"   Found {len(existing_keys)} tickets already in database")
    print()
    
    try:
        # Connect to Jira using REST API v3
        print("🔌 Connecting to Jira...")
        auth = HTTPBasicAuth(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        print("   ✅ Connected!")
        print()
        
        # Fetch all tickets (including closed, done, resolved, etc.)
        # We'll fetch ALL tickets from CO project, not just closed ones
        print("🔍 Fetching ALL tickets from Jira CO project...")
        print("   (This includes tickets in all statuses)")
        print()
        
        # JQL to get all tickets from CO project, ordered by creation date
        jql = f'project = {Config.JIRA_PROJECT_KEY} ORDER BY created ASC'
        
        # Use REST API v3 /search endpoint
        url = f'{Config.JIRA_URL}/rest/api/3/search'
        
        # Fetch tickets in batches
        all_issues = []
        start_at = 0
        batch_size = 100  # Jira API max is 100 per request
        total_in_jira = None
        
        while True:
            payload = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': batch_size,
                'fields': ['key', 'id', 'summary', 'status', 'project', 'created', 'updated']
            }
            
            try:
                response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                
                # Get total count on first request
                if total_in_jira is None:
                    total_in_jira = data.get('total', 0)
                    print(f"   📊 Total tickets in Jira: {total_in_jira}")
                    print()
                
                issues = data.get('issues', [])
                
                if not issues:
                    break
                
                all_issues.extend(issues)
                current_count = len(all_issues)
                
                print(f"   📦 Fetched batch: {start_at + 1} to {start_at + len(issues)} tickets (Total: {current_count}/{total_in_jira})")
                
                # Check if we've fetched all tickets
                if len(issues) < batch_size or current_count >= total_in_jira:
                    break
                
                start_at += batch_size
                
                # Small delay to avoid rate limiting
                time.sleep(0.3)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching tickets: {str(e)}")
                print(f"   ⚠️  Error fetching batch: {str(e)}")
                break
        
        print()
        print(f"✅ Successfully fetched {len(all_issues)} tickets from Jira")
        print()
        
        if len(all_issues) == 0:
            print("⚠️  No tickets found in CO project.")
            return
        
        # Filter out tickets that already exist
        new_tickets = []
        for issue in all_issues:
            key = issue.get('key')
            if key not in existing_keys:
                new_tickets.append(issue)
        
        print(f"📋 Summary:")
        print(f"   - Total tickets in Jira: {len(all_issues)}")
        print(f"   - Already in Weaviate: {len(all_issues) - len(new_tickets)}")
        print(f"   - New tickets to import: {len(new_tickets)}")
        print()
        
        if len(new_tickets) == 0:
            print("✅ All tickets are already in Weaviate!")
            return
        
        # Show sample of tickets to import
        print("📝 Sample tickets to import:")
        for issue in new_tickets[:10]:
            key = issue.get('key')
            summary = issue.get('fields', {}).get('summary', 'No summary')[:50]
            status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
            print(f"   - {key}: {summary}... [{status}]")
        if len(new_tickets) > 10:
            print(f"   ... and {len(new_tickets) - 10} more")
        print()
        
        # Ask for confirmation
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
        skipped_count = 0
        
        for i, issue in enumerate(new_tickets, 1):
            issue_key = issue.get('key')
            issue_id = issue.get('id')
            project_key = issue.get('fields', {}).get('project', {}).get('key', '')
            status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
            
            # Double-check it's from CO project
            if project_key != Config.JIRA_PROJECT_KEY:
                print(f"[{i}/{len(new_tickets)}] ⏭️  Skipping {issue_key} (project: {project_key})")
                skipped_count += 1
                continue
            
            print(f"[{i}/{len(new_tickets)}] Processing {issue_key} [{status}]...", end=" ")
            
            try:
                # Fetch full ticket details using the issue ID
                issue_details = jira_service.get_issue_details(issue_id)
                
                # Store in Weaviate
                issue_uuid = weaviate_service.insert_issue(issue_details)
                
                summary = issue.get('fields', {}).get('summary', 'No summary')[:45]
                print(f"✅ Stored - {summary}...")
                success_count += 1
                
                # Small delay every 10 tickets to avoid overwhelming the API
                if i % 10 == 0:
                    time.sleep(0.3)
                
            except Exception as e:
                error_msg = str(e)[:50]
                print(f"❌ Error: {error_msg}")
                error_count += 1
                logger.error(f"Error processing {issue_key}: {str(e)}")
        
        print()
        print("=" * 70)
        print("📊 FINAL SUMMARY")
        print("=" * 70)
        print()
        print(f"✅ Successfully stored: {success_count} tickets")
        if skipped_count > 0:
            print(f"⏭️  Skipped (wrong project): {skipped_count} tickets")
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
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        print("❌ Failed to fetch tickets. Check the error above.")

if __name__ == "__main__":
    fetch_all_tickets_from_jira()

