#!/usr/bin/env python3
"""
Fetch all existing closed tickets from CO project and store them in Weaviate
"""

from config import Config
from services.jira_service import JiraService
from services.weaviate_service import WeaviateService
from jira import JIRA
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_all_closed_tickets():
    """Fetch all closed tickets from CO project using Jira Python library"""
    print("=" * 70)
    print("📥 FETCHING EXISTING CLOSED TICKETS - Critical Ops (CO Project)")
    print("=" * 70)
    print()
    
    try:
        # Connect to Jira
        print("🔌 Connecting to Jira...")
        jira = JIRA(
            server=Config.JIRA_URL,
            basic_auth=(Config.JIRA_USERNAME, Config.JIRA_API_TOKEN)
        )
        print("   ✅ Connected!")
        print()
        
        # Search for closed tickets
        print(f"🔍 Searching for closed tickets in CO project...")
        jql = f'project = CO AND status = Closed ORDER BY updated DESC'
        
        # Get total count first
        issues = jira.search_issues(jql, maxResults=0)
        total = len(issues) if hasattr(issues, '__len__') else 0
        
        # Actually fetch them (in batches)
        print(f"   Found tickets to process...")
        print()
        
        all_issues = []
        start_at = 0
        batch_size = 50
        
        while True:
            issues_batch = jira.search_issues(
                jql, 
                startAt=start_at, 
                maxResults=batch_size,
                fields=['summary', 'status', 'project', 'key', 'description', 'comment', 
                       'priority', 'labels', 'assignee', 'reporter', 'created', 'updated', 
                       'resolutiondate', 'attachment']
            )
            
            if not issues_batch:
                break
                
            all_issues.extend(issues_batch)
            print(f"   📦 Fetched batch: {start_at + 1} to {start_at + len(issues_batch)} tickets")
            
            if len(issues_batch) < batch_size:
                break
                
            start_at += batch_size
        
        total_fetched = len(all_issues)
        print()
        print(f"✅ Successfully fetched {total_fetched} closed tickets")
        print()
        
        if total_fetched == 0:
            print("⚠️  No closed tickets found in CO project.")
            print("   Make sure you have closed some tickets in your Critical Ops board.")
            return
        
        # Initialize services
        print("💾 Initializing storage services...")
        jira_service = JiraService(
            Config.JIRA_URL,
            Config.JIRA_USERNAME,
            Config.JIRA_API_TOKEN
        )
        weaviate_service = WeaviateService()
        
        print("   ✅ Ready to store tickets")
        print()
        print("=" * 70)
        print("📝 PROCESSING AND STORING TICKETS")
        print("=" * 70)
        print()
        
        # Process each ticket
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, issue in enumerate(all_issues, 1):
            issue_key = issue.key
            issue_id = issue.id
            project_key = issue.fields.project.key
            
            # Double-check it's from CO project
            if project_key != 'CO':
                print(f"[{i}/{total_fetched}] ⏭️  Skipping {issue_key} (project: {project_key})")
                skipped_count += 1
                continue
            
            print(f"[{i}/{total_fetched}] Processing {issue_key}...", end=" ")
            
            try:
                # Fetch full ticket details using the issue ID
                issue_details = jira_service.get_issue_details(issue_id)
                
                # Store in Weaviate
                issue_uuid = weaviate_service.insert_issue(issue_details)
                
                summary = issue.fields.summary[:50] if issue.fields.summary else "No summary"
                print(f"✅ Stored - {summary}...")
                success_count += 1
                
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
        print(f"📈 Database now contains: {success_count} tickets from Critical Ops")
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
    fetch_all_closed_tickets()



