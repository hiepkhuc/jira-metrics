#!/usr/bin/env python3
"""
JIRA Metrics Extractor for Weekly Team Reporting

Extracts metrics from JIRA Cloud for Kanban teams:
- Throughput, Cycle Time, Lead Time
- WIP, Status Distribution, Issue Types
- Assignee Workload, Story Points
- Aging WIP Analysis
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

# Config loaded flag
CONFIG_LOADED = False

# Config defaults (overridden by config file)
JIRA_URL = ""
JIRA_EMAIL = ""
JIRA_API_TOKEN = ""
STORY_POINTS_FIELD = "customfield_10016"
IN_PROGRESS_STATUSES = ["In Progress", "In Review", "Code Review", "Testing", "QA", "Correction Required"]
WIP_HEALTH_STATUSES = ["To Do"] + [s for s in IN_PROGRESS_STATUSES if s != "To Do"]
DONE_STATUSES = ["Done", "Closed", "Resolved", "Complete"]
AGING_WARNING_DAYS = 14
AGING_CRITICAL_DAYS = 30
OUTPUT_DIR = "output"
DEFAULT_MONTHS = 6
CONFLUENCE_SPACE_KEY = "ENG"
CONFLUENCE_ROOT_PAGE_TITLE = "JIRA Metrics Reports"
ISSUE_TYPES = ["Bug", "Improvement", "Story", "Task", "Sub-task"]


def load_dependencies():
    """Load config file. Called before actual work."""
    global CONFIG_LOADED
    global JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, STORY_POINTS_FIELD
    global IN_PROGRESS_STATUSES, WIP_HEALTH_STATUSES, DONE_STATUSES
    global AGING_WARNING_DAYS, AGING_CRITICAL_DAYS, OUTPUT_DIR, DEFAULT_MONTHS
    global CONFLUENCE_SPACE_KEY, CONFLUENCE_ROOT_PAGE_TITLE
    global ISSUE_TYPES

    if CONFIG_LOADED:
        return True

    # Try to import local config, fall back to template
    try:
        from config_local import (
            JIRA_URL as url,
            JIRA_EMAIL as email,
            JIRA_API_TOKEN as token,
            STORY_POINTS_FIELD as sp_field,
            IN_PROGRESS_STATUSES as ip_statuses,
            DONE_STATUSES as done_statuses,
            AGING_WARNING_DAYS as warn_days,
            AGING_CRITICAL_DAYS as crit_days,
            OUTPUT_DIR as out_dir,
            DEFAULT_MONTHS as def_months,
            CONFLUENCE_SPACE_KEY as conf_space,
            CONFLUENCE_ROOT_PAGE_TITLE as conf_root,
            ISSUE_TYPES as issue_types,
        )
        JIRA_URL = url
        JIRA_EMAIL = email
        JIRA_API_TOKEN = token
        STORY_POINTS_FIELD = sp_field
        IN_PROGRESS_STATUSES = ip_statuses
        WIP_HEALTH_STATUSES = ["To Do"] + [s for s in IN_PROGRESS_STATUSES if s != "To Do"]
        DONE_STATUSES = done_statuses
        AGING_WARNING_DAYS = warn_days
        AGING_CRITICAL_DAYS = crit_days
        OUTPUT_DIR = out_dir
        DEFAULT_MONTHS = def_months
        CONFLUENCE_SPACE_KEY = conf_space
        CONFLUENCE_ROOT_PAGE_TITLE = conf_root
        ISSUE_TYPES = issue_types
    except ImportError:
        try:
            from config import (
                JIRA_URL as url,
                JIRA_EMAIL as email,
                JIRA_API_TOKEN as token,
                STORY_POINTS_FIELD as sp_field,
                IN_PROGRESS_STATUSES as ip_statuses,
                DONE_STATUSES as done_statuses,
                AGING_WARNING_DAYS as warn_days,
                AGING_CRITICAL_DAYS as crit_days,
                OUTPUT_DIR as out_dir,
                DEFAULT_MONTHS as def_months,
                CONFLUENCE_SPACE_KEY as conf_space,
                CONFLUENCE_ROOT_PAGE_TITLE as conf_root,
                ISSUE_TYPES as issue_types,
            )
            JIRA_URL = url
            JIRA_EMAIL = email
            JIRA_API_TOKEN = token
            STORY_POINTS_FIELD = sp_field
            IN_PROGRESS_STATUSES = ip_statuses
            WIP_HEALTH_STATUSES = ["To Do"] + [s for s in IN_PROGRESS_STATUSES if s != "To Do"]
            DONE_STATUSES = done_statuses
            AGING_WARNING_DAYS = warn_days
            AGING_CRITICAL_DAYS = crit_days
            OUTPUT_DIR = out_dir
            DEFAULT_MONTHS = def_months
            CONFLUENCE_SPACE_KEY = conf_space
            CONFLUENCE_ROOT_PAGE_TITLE = conf_root
            ISSUE_TYPES = issue_types
        except ImportError:
            print("Error: No config file found. Create config.py or config_local.py")
            return False

    CONFIG_LOADED = True
    return True


class JiraMetricsExtractor:
    """Extract and calculate JIRA metrics for team reporting."""

    def __init__(self, months: int = 6, verbose: bool = False, output_dir: str = None,
                 generate_charts: bool = False, bug_history: bool = False,
                 confluence: bool = False):
        self.months = months
        self.verbose = verbose
        self.output_dir = output_dir or OUTPUT_DIR
        self.generate_charts = generate_charts
        self.bug_history = bug_history
        self.confluence = confluence
        self.issues = []
        self.all_bugs = []
        self.start_date = datetime.now() - timedelta(days=months * 30)

    def log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[INFO] {message}")

    def connect(self) -> bool:
        """Establish connection to JIRA Cloud."""
        import requests
        from requests.auth import HTTPBasicAuth

        try:
            self.log(f"Connecting to {JIRA_URL}...")

            # Test connection with myself endpoint
            url = f"{JIRA_URL}/rest/api/3/myself"
            auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
            response = requests.get(url, auth=auth)
            response.raise_for_status()

            user = response.json()
            self.log(f"Connected as {user.get('displayName', 'Unknown')}!")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"Error connecting to JIRA: {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"Error connecting to JIRA: {e}")
            return False

    def fetch_issues(self) -> list:
        """Fetch all issues from JIRA within the time range."""
        import requests
        from requests.auth import HTTPBasicAuth

        start_str = self.start_date.strftime("%Y-%m-%d")

        # JQL to get all issues created or updated in the time range
        # Filter to configured issue types
        type_list = ", ".join(f'"{t}"' for t in ISSUE_TYPES)
        jql = (
            f'(created >= "{start_str}" OR '
            f'status changed DURING ("{start_str}", now())) '
            f'AND issuetype IN ({type_list}) '
            f'ORDER BY created DESC'
        )

        self.log(f"Fetching issues since {start_str}...")

        all_issues = []
        start_at = 0
        max_results = 100

        # Use the new v3 search/jql endpoint
        url = f"{JIRA_URL}/rest/api/3/search/jql"
        auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        next_page_token = None

        while True:
            try:
                payload = {
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": [
                        "summary", "status", "issuetype", "priority", "assignee",
                        "reporter", "created", "updated", "project", "labels",
                        "components", STORY_POINTS_FIELD,
                    ],
                    "expand": "changelog",
                }

                # Add pagination token if we have one
                if next_page_token:
                    payload["nextPageToken"] = next_page_token

                response = requests.post(url, json=payload, headers=headers, auth=auth)

                # Capture response before raising
                if response.status_code != 200:
                    print(f"Error fetching issues: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                    break

                data = response.json()

                issues = data.get("issues", [])
                if not issues:
                    break

                all_issues.extend(issues)
                self.log(f"Fetched {len(all_issues)} issues...")

                # Check for next page
                next_page_token = data.get("nextPageToken")
                if not next_page_token or data.get("isLast", True):
                    break

            except Exception as e:
                print(f"Error fetching issues: {e}")
                break

        self.issues = all_issues
        self.log(f"Total issues fetched: {len(self.issues)}")
        return self.issues

    def fetch_all_bugs(self) -> list:
        """Fetch all bugs from JIRA (no time filter) for cumulative analysis."""
        import requests
        from requests.auth import HTTPBasicAuth

        # JQL to get all bugs, ordered by creation date
        jql = 'issuetype = Bug ORDER BY created ASC'

        self.log("Fetching all bugs for cumulative analysis...")

        all_bugs = []
        url = f"{JIRA_URL}/rest/api/3/search/jql"
        auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        next_page_token = None

        while True:
            try:
                payload = {
                    "jql": jql,
                    "maxResults": 100,
                    "fields": ["created", "resolutiondate", "status", "updated"],
                }

                if next_page_token:
                    payload["nextPageToken"] = next_page_token

                response = requests.post(url, json=payload, headers=headers, auth=auth)

                if response.status_code != 200:
                    print(f"Error fetching bugs: HTTP {response.status_code}")
                    break

                data = response.json()
                issues = data.get("issues", [])
                if not issues:
                    break

                all_bugs.extend(issues)
                self.log(f"Fetched {len(all_bugs)} bugs...")

                next_page_token = data.get("nextPageToken")
                if not next_page_token or data.get("isLast", True):
                    break

            except Exception as e:
                print(f"Error fetching bugs: {e}")
                break

        self.all_bugs = all_bugs
        self.log(f"Total bugs fetched: {len(self.all_bugs)}")
        return self.all_bugs

    def calculate_bug_cumulative(self) -> list:
        """Calculate cumulative bug data from all bugs."""
        from collections import defaultdict

        # Group by week
        created_by_week = defaultdict(int)
        resolved_by_week = defaultdict(int)

        for bug in self.all_bugs:
            fields = bug.get("fields", {})

            # Created date
            created_str = fields.get("created", "")[:10]
            if created_str:
                created_date = datetime.strptime(created_str, "%Y-%m-%d")
                created_week = created_date.strftime("%Y-W%W")
                created_by_week[created_week] += 1

            # Check if bug is resolved by status (not just resolutiondate)
            status = fields.get("status", {})
            status_name = status.get("name", "")
            status_category = status.get("statusCategory", {}).get("name", "")

            is_resolved = status_name in DONE_STATUSES or status_category == "Done"

            if is_resolved:
                # Use resolutiondate if available, otherwise fall back to updated date
                resolution_str = fields.get("resolutiondate")
                if not resolution_str:
                    resolution_str = fields.get("updated")

                if resolution_str:
                    resolved_date = datetime.strptime(resolution_str[:10], "%Y-%m-%d")
                    resolved_week = resolved_date.strftime("%Y-W%W")
                    resolved_by_week[resolved_week] += 1

        # Get all weeks and sort
        all_weeks = sorted(set(created_by_week.keys()) | set(resolved_by_week.keys()))

        # Calculate cumulative values
        cumulative_data = []
        cum_created = 0
        cum_resolved = 0

        for week in all_weeks:
            created_this_week = created_by_week.get(week, 0)
            resolved_this_week = resolved_by_week.get(week, 0)

            cum_created += created_this_week
            cum_resolved += resolved_this_week

            cumulative_data.append({
                "week": week,
                "created_this_week": created_this_week,
                "resolved_this_week": resolved_this_week,
                "cumulative_created": cum_created,
                "cumulative_resolved": cum_resolved,
                "open_bugs": cum_created - cum_resolved,
            })

        return cumulative_data

    def get_status_change_date(self, issue: dict, to_statuses: list) -> Optional[datetime]:
        """Get the date when issue moved to one of the specified statuses."""
        changelog = issue.get("changelog")
        if not changelog:
            return None

        for history in changelog.get("histories", []):
            for item in history.get("items", []):
                if item.get("field") == "status" and item.get("toString") in to_statuses:
                    return datetime.strptime(
                        history["created"][:19], "%Y-%m-%dT%H:%M:%S"
                    )
        return None

    def get_first_in_progress_date(self, issue: dict) -> Optional[datetime]:
        """Get the date when issue first moved to In Progress."""
        changelog = issue.get("changelog")
        if not changelog:
            return None

        histories = sorted(
            changelog.get("histories", []),
            key=lambda h: h.get("created", ""),
        )
        for history in histories:
            for item in history.get("items", []):
                if item.get("field") == "status" and item.get("toString") in IN_PROGRESS_STATUSES:
                    return datetime.strptime(
                        history["created"][:19], "%Y-%m-%dT%H:%M:%S"
                    )
        return None

    def get_done_date(self, issue: dict) -> Optional[datetime]:
        """Get the date when issue moved to Done."""
        return self.get_status_change_date(issue, DONE_STATUSES)

    def get_correction_required_dates(self, issue: dict) -> list:
        """Get all dates when issue moved to 'Correction Required' status."""
        changelog = issue.get("changelog")
        if not changelog:
            return []

        dates = []
        for history in changelog.get("histories", []):
            for item in history.get("items", []):
                if item.get("field") == "status" and item.get("toString") == "Correction Required":
                    date = datetime.strptime(history["created"][:19], "%Y-%m-%dT%H:%M:%S")
                    dates.append(date)
        return dates

    def get_story_points(self, issue: dict) -> Optional[float]:
        """Extract story points from custom field."""
        try:
            fields = issue.get("fields", {})
            points = fields.get(STORY_POINTS_FIELD)
            return float(points) if points is not None else None
        except (TypeError, ValueError):
            return None

    def parse_issue(self, issue: dict) -> dict:
        """Parse a JIRA issue JSON into a flat dictionary."""
        fields = issue.get("fields", {})
        created_str = fields.get("created", "")[:19]
        created = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%S") if created_str else datetime.now()

        in_progress_date = self.get_first_in_progress_date(issue)
        done_date = self.get_done_date(issue)

        # Calculate cycle time (In Progress -> Done)
        cycle_time = None
        if in_progress_date and done_date and done_date > in_progress_date:
            cycle_time = (done_date - in_progress_date).days

        # Calculate lead time (Created -> Done)
        lead_time = None
        if done_date:
            lead_time = (done_date - created).days

        # Calculate aging (for WIP items)
        aging_days = None
        status_obj = fields.get("status", {})
        status = status_obj.get("name", "Unknown") if status_obj else "Unknown"
        if status in IN_PROGRESS_STATUSES and status != "To Do":
            if in_progress_date:
                aging_days = (datetime.now() - in_progress_date).days
            else:
                aging_days = (datetime.now() - created).days

        # Extract nested fields safely
        project = fields.get("project", {})
        issuetype = fields.get("issuetype", {})
        priority = fields.get("priority", {})
        assignee = fields.get("assignee", {})
        reporter = fields.get("reporter", {})
        components = fields.get("components", [])
        labels = fields.get("labels", [])

        return {
            "key": issue.get("key", ""),
            "project": project.get("key", "") if project else "",
            "summary": fields.get("summary", ""),
            "issue_type": issuetype.get("name", "Unknown") if issuetype else "Unknown",
            "status": status,
            "priority": priority.get("name", "None") if priority else "None",
            "assignee": assignee.get("displayName", "Unassigned") if assignee else "Unassigned",
            "reporter": reporter.get("displayName", "Unknown") if reporter else "Unknown",
            "created": created.strftime("%Y-%m-%d"),
            "created_week": created.strftime("%Y-W%W"),
            "in_progress_date": in_progress_date.strftime("%Y-%m-%d") if in_progress_date else "",
            "done_date": done_date.strftime("%Y-%m-%d") if done_date else "",
            "done_week": done_date.strftime("%Y-W%W") if done_date else "",
            "story_points": self.get_story_points(issue),
            "cycle_time_days": cycle_time,
            "lead_time_days": lead_time,
            "aging_days": aging_days,
            "labels": ",".join(labels) if labels else "",
            "components": ",".join(c.get("name", "") for c in components) if components else "",
        }

    def calculate_metrics(self) -> dict:
        """Calculate all metrics from fetched issues."""
        self.log("Calculating metrics...")

        parsed_issues = [self.parse_issue(issue) for issue in self.issues]

        # Weekly throughput
        throughput = defaultdict(lambda: {"count": 0, "story_points": 0})
        for issue in parsed_issues:
            if issue["done_week"]:
                throughput[issue["done_week"]]["count"] += 1
                if issue["story_points"]:
                    throughput[issue["done_week"]]["story_points"] += issue["story_points"]

        # Status distribution
        status_dist = defaultdict(int)
        for issue in parsed_issues:
            status_dist[issue["status"]] += 1

        # Issue type breakdown
        type_breakdown = defaultdict(int)
        for issue in parsed_issues:
            type_breakdown[issue["issue_type"]] += 1

        # Assignee workload (3 categories: To Do, In Progress, Done)
        assignee_wip = defaultdict(lambda: {"to_do": 0, "in_progress": 0, "done": 0})
        for issue in parsed_issues:
            if issue["status"] == "To Do":
                assignee_wip[issue["assignee"]]["to_do"] += 1
            elif issue["status"] in IN_PROGRESS_STATUSES:
                assignee_wip[issue["assignee"]]["in_progress"] += 1
            elif issue["status"] in DONE_STATUSES:
                assignee_wip[issue["assignee"]]["done"] += 1

        # Cycle time by week
        cycle_time_weekly = defaultdict(list)
        for issue in parsed_issues:
            if issue["done_week"] and issue["cycle_time_days"] is not None:
                cycle_time_weekly[issue["done_week"]].append(issue["cycle_time_days"])

        # Lead time by week
        lead_time_weekly = defaultdict(list)
        for issue in parsed_issues:
            if issue["done_week"] and issue["lead_time_days"] is not None:
                lead_time_weekly[issue["done_week"]].append(issue["lead_time_days"])

        # Aging WIP
        aging_wip = [
            issue for issue in parsed_issues
            if issue["aging_days"] is not None and issue["aging_days"] > 0
        ]

        # Bugs created weekly (with priority breakdown)
        bugs_created = defaultdict(lambda: {
            "total": 0, "critical": 0, "highest": 0, "high": 0, "medium": 0, "low": 0
        })
        for issue in parsed_issues:
            if issue["issue_type"] == "Bug":
                week = issue["created_week"]
                bugs_created[week]["total"] += 1
                priority = issue["priority"].lower()
                if priority == "highest":
                    bugs_created[week]["highest"] += 1
                elif priority == "critical":
                    bugs_created[week]["critical"] += 1
                elif priority == "high":
                    bugs_created[week]["high"] += 1
                elif priority == "medium":
                    bugs_created[week]["medium"] += 1
                else:
                    bugs_created[week]["low"] += 1

        # Throughput by team member (weekly)
        throughput_by_member = defaultdict(lambda: defaultdict(int))
        for issue in parsed_issues:
            if issue["done_week"] and issue["assignee"] != "Unassigned":
                throughput_by_member[issue["done_week"]][issue["assignee"]] += 1

        # WIP Health: breakdown by assignee and WIP status (includes To Do)
        wip_health = defaultdict(lambda: defaultdict(int))
        for issue in parsed_issues:
            status = issue["status"]
            if status in WIP_HEALTH_STATUSES:
                wip_health[issue["assignee"]][status] += 1

        return {
            "all_issues": parsed_issues,
            "throughput": dict(throughput),
            "status_distribution": dict(status_dist),
            "type_breakdown": dict(type_breakdown),
            "assignee_workload": dict(assignee_wip),
            "cycle_time_weekly": dict(cycle_time_weekly),
            "lead_time_weekly": dict(lead_time_weekly),
            "aging_wip": aging_wip,
            "bugs_created_weekly": dict(bugs_created),
            "throughput_by_member": {k: dict(v) for k, v in throughput_by_member.items()},
            "wip_health": {k: dict(v) for k, v in wip_health.items()},
        }

    def export_csv(self, metrics: dict) -> None:
        """Export all metrics to CSV files."""
        os.makedirs(self.output_dir, exist_ok=True)
        self.log(f"Exporting CSV files to {self.output_dir}/...")

        # 1. All issues (raw data)
        self._write_csv(
            f"{self.output_dir}/issues_all.csv",
            metrics["all_issues"],
            [
                "key", "project", "summary", "issue_type", "status", "priority",
                "assignee", "reporter", "created", "created_week",
                "in_progress_date", "done_date", "done_week", "story_points",
                "cycle_time_days", "lead_time_days", "aging_days", "labels", "components",
            ],
        )

        # 2. Weekly throughput
        throughput_rows = [
            {
                "week": week,
                "issues_completed": data["count"],
                "story_points_completed": data["story_points"],
            }
            for week, data in sorted(metrics["throughput"].items())
        ]
        self._write_csv(
            f"{self.output_dir}/weekly_throughput.csv",
            throughput_rows,
            ["week", "issues_completed", "story_points_completed"],
        )

        # 3. Status distribution
        status_rows = [
            {"status": status, "count": count}
            for status, count in sorted(
                metrics["status_distribution"].items(),
                key=lambda x: -x[1],
            )
        ]
        self._write_csv(
            f"{self.output_dir}/status_distribution.csv",
            status_rows,
            ["status", "count"],
        )

        # 4. Assignee workload (To Do, In Progress, Done)
        excluded_assignees = ["Steve Hanov", "Aaron Martens"]
        workload_rows = [
            {
                "assignee": assignee,
                "to_do": data["to_do"],
                "in_progress": data["in_progress"],
                "done": data["done"],
            }
            for assignee, data in sorted(
                metrics["assignee_workload"].items(),
                key=lambda x: -(x[1]["to_do"] + x[1]["in_progress"] + x[1]["done"]),
            )
            if assignee not in excluded_assignees
        ]
        self._write_csv(
            f"{self.output_dir}/assignee_workload.csv",
            workload_rows,
            ["assignee", "to_do", "in_progress", "done"],
        )

        # 5. Issue types
        type_rows = [
            {"issue_type": itype, "count": count}
            for itype, count in sorted(
                metrics["type_breakdown"].items(),
                key=lambda x: -x[1],
            )
        ]
        self._write_csv(
            f"{self.output_dir}/issue_types.csv",
            type_rows,
            ["issue_type", "count"],
        )

        # 6. Cycle time weekly
        cycle_rows = []
        for week, times in sorted(metrics["cycle_time_weekly"].items()):
            if times:
                avg_cycle = sum(times) / len(times)
                min_cycle = min(times)
                max_cycle = max(times)
                median_cycle = sorted(times)[len(times) // 2]
            else:
                avg_cycle = min_cycle = max_cycle = median_cycle = 0
            cycle_rows.append({
                "week": week,
                "avg_cycle_time_days": round(avg_cycle, 1),
                "min_cycle_time_days": min_cycle,
                "max_cycle_time_days": max_cycle,
                "median_cycle_time_days": median_cycle,
                "issues_count": len(times),
            })
        self._write_csv(
            f"{self.output_dir}/cycle_time_weekly.csv",
            cycle_rows,
            ["week", "avg_cycle_time_days", "min_cycle_time_days",
             "max_cycle_time_days", "median_cycle_time_days", "issues_count"],
        )

        # 7. Lead time weekly
        lead_rows = []
        for week, times in sorted(metrics["lead_time_weekly"].items()):
            if times:
                avg_lead = sum(times) / len(times)
                min_lead = min(times)
                max_lead = max(times)
                median_lead = sorted(times)[len(times) // 2]
            else:
                avg_lead = min_lead = max_lead = median_lead = 0
            lead_rows.append({
                "week": week,
                "avg_lead_time_days": round(avg_lead, 1),
                "min_lead_time_days": min_lead,
                "max_lead_time_days": max_lead,
                "median_lead_time_days": median_lead,
                "issues_count": len(times),
            })
        self._write_csv(
            f"{self.output_dir}/lead_time_weekly.csv",
            lead_rows,
            ["week", "avg_lead_time_days", "min_lead_time_days",
             "max_lead_time_days", "median_lead_time_days", "issues_count"],
        )

        # 8. Aging WIP
        aging_rows = sorted(
            [
                {
                    "key": issue["key"],
                    "summary": issue["summary"],
                    "status": issue["status"],
                    "assignee": issue["assignee"],
                    "in_progress_date": issue["in_progress_date"],
                    "aging_days": issue["aging_days"],
                    "severity": (
                        "CRITICAL" if issue["aging_days"] >= AGING_CRITICAL_DAYS
                        else "WARNING" if issue["aging_days"] >= AGING_WARNING_DAYS
                        else "OK"
                    ),
                }
                for issue in metrics["aging_wip"]
            ],
            key=lambda x: -x["aging_days"],
        )
        self._write_csv(
            f"{self.output_dir}/aging_wip.csv",
            aging_rows,
            ["key", "summary", "status", "assignee", "in_progress_date",
             "aging_days", "severity"],
        )

        # 9. Bugs created weekly (filtered to last N months)
        cutoff_date = datetime.now() - timedelta(days=self.months * 30)
        bugs_rows = []
        for week, data in sorted(metrics["bugs_created_weekly"].items()):
            # Parse week string (YYYY-Www) to date
            try:
                week_date = datetime.strptime(week + "-1", "%Y-W%W-%w")
            except ValueError:
                week_date = datetime.strptime(week + "-1", "%G-W%V-%u")
            if week_date >= cutoff_date:
                bugs_rows.append({
                    "week": week,
                    "bugs_created": data["total"],
                    "priority_critical": data["critical"],
                    "priority_highest": data["highest"],
                    "priority_high": data["high"],
                    "priority_medium": data["medium"],
                    "priority_low": data["low"],
                })
        self._write_csv(
            f"{self.output_dir}/bugs_created_weekly.csv",
            bugs_rows,
            ["week", "bugs_created", "priority_critical", "priority_highest",
             "priority_high", "priority_medium", "priority_low"],
        )

        # 10. Throughput by team member
        member_rows = []
        for week, members in sorted(metrics["throughput_by_member"].items()):
            for assignee, count in sorted(members.items(), key=lambda x: -x[1]):
                if assignee not in excluded_assignees:
                    member_rows.append({
                        "week": week,
                        "assignee": assignee,
                        "issues_completed": count,
                    })
        self._write_csv(
            f"{self.output_dir}/throughput_by_member.csv",
            member_rows,
            ["week", "assignee", "issues_completed"],
        )

        # 11. WIP Health by assignee and status (includes To Do)
        wip_rows = []
        for assignee, statuses in sorted(metrics["wip_health"].items()):
            if assignee in excluded_assignees:
                continue
            row = {"assignee": assignee}
            total = 0
            for status in WIP_HEALTH_STATUSES:
                count = statuses.get(status, 0)
                row[status.replace(" ", "_")] = count
                total += count
            row["Total"] = total
            wip_rows.append(row)
        self._write_csv(
            f"{self.output_dir}/wip_health.csv",
            wip_rows,
            ["assignee"] + [s.replace(" ", "_") for s in WIP_HEALTH_STATUSES] + ["Total"],
        )

        self.log("CSV export complete!")

    def export_bug_cumulative_csv(self, cumulative_data: list) -> None:
        """Export cumulative bug data to CSV."""
        os.makedirs(self.output_dir, exist_ok=True)
        self._write_csv(
            f"{self.output_dir}/bugs_cumulative.csv",
            cumulative_data,
            ["week", "created_this_week", "resolved_this_week",
             "cumulative_created", "cumulative_resolved", "open_bugs"],
        )

    def _write_csv(self, filepath: str, rows: list, fieldnames: list) -> None:
        """Write rows to a CSV file."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        self.log(f"  Written: {filepath} ({len(rows)} rows)")

    def print_summary(self, metrics: dict) -> None:
        """Print a summary of the metrics to console."""
        print("\n" + "=" * 60)
        print("JIRA METRICS SUMMARY")
        print("=" * 60)

        print(f"\nTotal Issues Analyzed: {len(metrics['all_issues'])}")

        # Status distribution
        print("\nStatus Distribution:")
        for status, count in sorted(
            metrics["status_distribution"].items(),
            key=lambda x: -x[1],
        )[:10]:
            print(f"  {status}: {count}")

        # Current WIP
        wip_count = sum(
            1 for issue in metrics["all_issues"]
            if issue["status"] in IN_PROGRESS_STATUSES
        )
        print(f"\nCurrent WIP (In Progress): {wip_count}")

        # Aging issues
        critical = sum(
            1 for issue in metrics["aging_wip"]
            if issue["aging_days"] >= AGING_CRITICAL_DAYS
        )
        warning = sum(
            1 for issue in metrics["aging_wip"]
            if AGING_WARNING_DAYS <= issue["aging_days"] < AGING_CRITICAL_DAYS
        )
        print(f"Aging WIP - Critical (>{AGING_CRITICAL_DAYS}d): {critical}")
        print(f"Aging WIP - Warning (>{AGING_WARNING_DAYS}d): {warning}")

        # Recent throughput
        sorted_weeks = sorted(metrics["throughput"].keys())[-4:]
        if sorted_weeks:
            print("\nRecent Weekly Throughput:")
            for week in sorted_weeks:
                data = metrics["throughput"][week]
                print(f"  {week}: {data['count']} issues, {data['story_points']} points")

        # Average cycle time
        all_cycle_times = [
            issue["cycle_time_days"]
            for issue in metrics["all_issues"]
            if issue["cycle_time_days"] is not None
        ]
        if all_cycle_times:
            avg_cycle = sum(all_cycle_times) / len(all_cycle_times)
            print(f"\nAverage Cycle Time: {avg_cycle:.1f} days")

        print("\n" + "=" * 60)
        print(f"CSV files exported to: {self.output_dir}/")
        print("=" * 60 + "\n")

    def run(self) -> bool:
        """Execute the full extraction pipeline."""
        if not load_dependencies():
            return False

        # Update output_dir if not explicitly set
        if self.output_dir == "output":
            self.output_dir = OUTPUT_DIR

        if not self.connect():
            return False

        self.fetch_issues()

        if not self.issues:
            print("No issues found in the specified time range.")
            return False

        metrics = self.calculate_metrics()
        self.export_csv(metrics)

        # Fetch and export cumulative bug data if requested
        bug_cumulative_data = None
        if self.bug_history:
            self.fetch_all_bugs()
            if self.all_bugs:
                bug_cumulative_data = self.calculate_bug_cumulative()
                self.export_bug_cumulative_csv(bug_cumulative_data)

        if self.generate_charts:
            self.log("Generating charts...")
            try:
                from charts import generate_all_charts
                generate_all_charts(self.output_dir, verbose=self.verbose, months=self.months,
                                    include_bug_cumulative=self.bug_history)
            except ImportError as e:
                print(f"Warning: Could not generate charts. Install dependencies: pip install matplotlib pandas")
                print(f"  Error: {e}")

        # Publish to Confluence if requested
        if self.confluence:
            self.log("Publishing to Confluence...")
            try:
                from confluence_publisher import ConfluencePublisher
                publisher = ConfluencePublisher(
                    base_url=JIRA_URL,
                    email=JIRA_EMAIL,
                    api_token=JIRA_API_TOKEN,
                    space_key=CONFLUENCE_SPACE_KEY,
                    root_page_title=CONFLUENCE_ROOT_PAGE_TITLE,
                )
                publisher.publish_report(
                    output_dir=self.output_dir,
                    months=self.months,
                    include_bug_cumulative=self.bug_history,
                    verbose=self.verbose,
                )
            except Exception as e:
                print(f"Warning: Failed to publish to Confluence: {e}")

        self.print_summary(metrics)
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Extract JIRA metrics for weekly team reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Extract last 6 months of data
  %(prog)s --months 3         # Extract last 3 months
  %(prog)s -v                 # Verbose output
  %(prog)s --output reports   # Custom output directory
  %(prog)s --charts           # Generate PNG charts
  %(prog)s --charts --confluence  # Generate charts and publish to Confluence

Output Files (CSV):
  issues_all.csv          - Raw issue data with all fields
  weekly_throughput.csv   - Issues and points completed per week
  status_distribution.csv - Count of issues by status
  assignee_workload.csv   - Current WIP per team member
  issue_types.csv         - Breakdown by issue type
  cycle_time_weekly.csv   - Cycle time statistics per week
  lead_time_weekly.csv    - Lead time statistics per week
  aging_wip.csv           - Items in progress too long
  bugs_created_weekly.csv - Bugs created per week by priority
  bugs_cumulative.csv     - Cumulative bug trend (with --bug-history)

Charts (with --charts flag):
  chart_throughput.png         - Weekly throughput bar/line chart
  chart_cycle_time.png         - Cycle time trend with min/max range
  chart_lead_time.png          - Lead time trend with min/max range
  chart_status_distribution.png - Status breakdown horizontal bars
  chart_issue_types.png        - Issue types donut chart
  chart_workload.png           - Assignee workload stacked bars
  chart_aging_wip.png          - Aging WIP by severity
  chart_bugs_created.png       - Bugs created weekly by priority
  chart_bugs_cumulative.png    - Cumulative bug trend (with --bug-history)
        """,
    )
    parser.add_argument(
        "-m", "--months",
        type=int,
        default=None,
        help="Number of months of data to extract (default: from config, usually 6)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help=f"Output directory for CSV files (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "-c", "--charts",
        action="store_true",
        help="Generate PNG charts from the CSV data",
    )
    parser.add_argument(
        "--bug-history",
        action="store_true",
        help="Fetch all bugs from beginning of time for cumulative trend chart",
    )
    parser.add_argument(
        "--confluence",
        action="store_true",
        help="Publish charts and analysis to a Confluence page",
    )

    # Load config first to get defaults
    load_dependencies()

    args = parser.parse_args()

    # Use config defaults if not specified on command line
    months = args.months if args.months is not None else DEFAULT_MONTHS
    output_dir = args.output if args.output else OUTPUT_DIR

    print(f"JIRA Metrics Extractor - Extracting {months} months of data")
    print("-" * 50)

    extractor = JiraMetricsExtractor(
        months=months,
        verbose=args.verbose,
        output_dir=output_dir,
        generate_charts=args.charts,
        bug_history=args.bug_history,
        confluence=args.confluence,
    )
    success = extractor.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
