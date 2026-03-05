# JIRA Configuration Template
# Copy this file to config_local.py and fill in your credentials

# JIRA Cloud URL (e.g., "https://yourcompany.atlassian.net")
JIRA_URL = "https://your-domain.atlassian.net"

# Your JIRA account email
JIRA_EMAIL = "your-email@example.com"

# API Token (generate at https://id.atlassian.com/manage-profile/security/api-tokens)
JIRA_API_TOKEN = "your-api-token-here"

# Custom field ID for Story Points (find via JIRA Admin > Issues > Custom Fields)
# Common defaults: "customfield_10016", "customfield_10026", "customfield_10004"
STORY_POINTS_FIELD = "customfield_10016"

# Status categories mapping (adjust to match your workflow)
# These determine which statuses count as "In Progress" or "Done"
IN_PROGRESS_STATUSES = [
    "In Progress",
    "In Review",
    "Awaiting Feedback",
    "Correction Required",
    "Testing",
    "In QA",
]

DONE_STATUSES = [
    "Done",
    "Archived"
]

# Issue types to include in metrics extraction
ISSUE_TYPES = [
    "Bug",
    "Improvement",
    "Story",
    "Task",
    "Sub-task",
]

# Aging WIP thresholds (days)
AGING_WARNING_DAYS = 14  # Items older than this are flagged
AGING_CRITICAL_DAYS = 30  # Items older than this are critical

# Output directory for CSV files
OUTPUT_DIR = "output"

# Default number of months to extract/display
DEFAULT_MONTHS = 6

# Confluence Publishing Settings
# Space key where reports will be published (e.g., "ENG")
CONFLUENCE_SPACE_KEY = "ENG"
# Parent page title under which report pages are created
CONFLUENCE_ROOT_PAGE_TITLE = "JIRA Metrics Reports"
