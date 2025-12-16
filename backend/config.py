import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Redis Configuration
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    
    # Celery Configuration with explicit Redis settings
    CELERY_BROKER_URL = f'redis://localhost:6379/0'  # Queue for tasks
    CELERY_RESULT_BACKEND = f'redis://localhost:6379/1'  # Store for results
    
    # Celery task settings
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_TRACK_STARTED = True  # Enable task tracking
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minute timeout
    
    # Weaviate Configuration
    # WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
    
    # JIRA Configuration
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    
    # Board/Project Filter - Only process tickets from this project
    JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'CO')  # Project key for "Critical Ops" board
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Must be set in .env file
