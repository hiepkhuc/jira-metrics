"""
Confluence report publisher for JIRA metrics.

Publishes charts and analysis text to a Confluence page.
"""

import os
import re
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth


# Chart-to-analysis mapping: (chart_filename, analysis_function_name, section_title)
CHART_SECTIONS = [
    ("chart_throughput.png", "analyze_throughput", "Throughput"),
    ("chart_throughput_by_member.png", "analyze_throughput_by_member", "Throughput by Member"),
    ("chart_wip_health.png", "analyze_wip_health", "WIP Health"),
    ("chart_workload.png", "analyze_workload", "Workload"),
    ("chart_cycle_time.png", "analyze_cycle_time", "Cycle Time"),
    ("chart_lead_time.png", "analyze_lead_time", "Lead Time"),
    ("chart_aging_wip.png", "analyze_aging_wip", "Aging WIP"),
    ("chart_status_distribution.png", "analyze_status_distribution", "Status Distribution"),
    ("chart_issue_types.png", "analyze_issue_types", "Issue Types"),
    ("chart_correction_required.png", "analyze_correction_required", "Correction Required"),
    ("chart_bugs_created.png", "analyze_bugs_created", "Bugs Created"),
]

CUMULATIVE_SECTION = ("chart_bugs_cumulative.png", "analyze_bugs_cumulative", "Bugs Cumulative")


class ConfluencePublisher:
    """Publish JIRA metrics charts and analysis to Confluence."""

    def __init__(self, base_url, email, api_token, space_key, root_page_title):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.space_key = space_key
        self.root_page_title = root_page_title
        self.api_base = f"{self.base_url}/wiki/rest/api/content"

    def _get_page_id_by_title(self, title):
        """Find a Confluence page by title and space key."""
        params = {
            "title": title,
            "spaceKey": self.space_key,
            "expand": "version",
        }
        resp = requests.get(self.api_base, params=params, auth=self.auth)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return results[0]["id"]
        return None

    def _create_page(self, title, body_html, parent_id=None):
        """Create a new Confluence page and return its ID."""
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": self.space_key},
            "body": {
                "storage": {
                    "value": body_html,
                    "representation": "storage",
                }
            },
        }
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]

        resp = requests.post(
            self.api_base,
            json=payload,
            auth=self.auth,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def _update_page(self, page_id, title, body_html):
        """Update an existing Confluence page body."""
        # Get current version
        resp = requests.get(f"{self.api_base}/{page_id}?expand=version", auth=self.auth)
        resp.raise_for_status()
        current_version = resp.json()["version"]["number"]

        payload = {
            "type": "page",
            "title": title,
            "body": {
                "storage": {
                    "value": body_html,
                    "representation": "storage",
                }
            },
            "version": {"number": current_version + 1},
        }

        resp = requests.put(
            f"{self.api_base}/{page_id}",
            json=payload,
            auth=self.auth,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()

    def _upload_attachment(self, page_id, file_path):
        """Upload a file as an attachment to a Confluence page."""
        filename = os.path.basename(file_path)
        url = f"{self.api_base}/{page_id}/child/attachment"

        # Check if attachment already exists
        resp = requests.get(url, auth=self.auth, params={"filename": filename})
        resp.raise_for_status()

        headers = {"X-Atlassian-Token": "nocheck"}
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "image/png")}
            existing = resp.json().get("results", [])
            if existing:
                # Update existing attachment
                att_id = existing[0]["id"]
                resp = requests.post(
                    f"{url}/{att_id}/data",
                    files=files,
                    headers=headers,
                    auth=self.auth,
                )
            else:
                resp = requests.post(
                    url,
                    files=files,
                    headers=headers,
                    auth=self.auth,
                )
        resp.raise_for_status()

    def _get_analysis_text(self, func_name, output_dir, months):
        """Call an analysis function from charts.py by name and return its text."""
        from charts import (
            analyze_throughput, analyze_cycle_time, analyze_lead_time,
            analyze_status_distribution, analyze_issue_types, analyze_workload,
            analyze_aging_wip, analyze_bugs_created, analyze_correction_required,
            analyze_throughput_by_member, analyze_wip_health, analyze_bugs_cumulative,
        )

        func_map = {
            "analyze_throughput": lambda: analyze_throughput(output_dir, months),
            "analyze_cycle_time": lambda: analyze_cycle_time(output_dir, months),
            "analyze_lead_time": lambda: analyze_lead_time(output_dir, months),
            "analyze_status_distribution": lambda: analyze_status_distribution(output_dir, months),
            "analyze_issue_types": lambda: analyze_issue_types(output_dir, months),
            "analyze_workload": lambda: analyze_workload(output_dir, weeks=6),
            "analyze_aging_wip": lambda: analyze_aging_wip(output_dir, months),
            "analyze_bugs_created": lambda: analyze_bugs_created(output_dir, months),
            "analyze_correction_required": lambda: analyze_correction_required(output_dir, months),
            "analyze_throughput_by_member": lambda: analyze_throughput_by_member(output_dir, weeks=6),
            "analyze_wip_health": lambda: analyze_wip_health(output_dir, months),
            "analyze_bugs_cumulative": lambda: analyze_bugs_cumulative(output_dir, months),
        }

        func = func_map.get(func_name)
        if func:
            return func() or ""
        return ""

    def _analysis_text_to_html(self, text):
        """Convert plain-text analysis output to rich Confluence storage format HTML."""
        parts = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r'^-{3,}$', stripped):
                continue
            if re.match(r'^[A-Z][A-Z /]+$', stripped):
                continue
            if stripped.startswith('\u26a0\ufe0f'):
                content = stripped.lstrip('\u26a0\ufe0f').strip()
                parts.append(
                    f'<ac:structured-macro ac:name="note">'
                    f'<ac:rich-text-body><p>{content}</p></ac:rich-text-body>'
                    f'</ac:structured-macro>'
                )
            elif stripped.startswith('Consider:'):
                parts.append(
                    f'<ac:structured-macro ac:name="tip">'
                    f'<ac:rich-text-body><p>{stripped}</p></ac:rich-text-body>'
                    f'</ac:structured-macro>'
                )
            else:
                parts.append(f'<p>{stripped}</p>')
        return '\n'.join(parts)

    def _build_section_html(self, title, chart_filename, analysis_text):
        """Build Confluence storage format HTML for one chart section."""
        html = f"<h2>{title}</h2>\n"
        html += (
            f'<ac:image ac:width="800">'
            f'<ri:attachment ri:filename="{chart_filename}"/>'
            f'</ac:image>\n'
        )
        if analysis_text:
            html += self._analysis_text_to_html(analysis_text) + '\n'
        return html

    def publish_report(self, output_dir, months, include_bug_cumulative=False, verbose=False):
        """Publish all charts and analysis to a new Confluence page.

        Args:
            output_dir: Directory containing chart PNGs and CSV data.
            months: Number of months of data (passed to analysis functions).
            include_bug_cumulative: Whether to include the cumulative bug chart.
            verbose: Print progress messages.
        """
        def log(msg):
            if verbose:
                print(f"[INFO] Confluence: {msg}")

        # 1. Find or create root page
        log(f"Looking for root page '{self.root_page_title}' in space '{self.space_key}'...")
        root_id = self._get_page_id_by_title(self.root_page_title)
        if not root_id:
            log("Root page not found, creating it...")
            root_id = self._create_page(
                self.root_page_title,
                "<p>Auto-generated parent page for JIRA Metrics reports.</p>",
            )
            log(f"Created root page (id={root_id})")
        else:
            log(f"Found root page (id={root_id})")

        # 2. Create child page with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        page_title = f"JIRA Metrics Report - {timestamp}"
        log(f"Creating report page: {page_title}")

        # Build sections
        sections = list(CHART_SECTIONS)
        if include_bug_cumulative:
            sections.append(CUMULATIVE_SECTION)

        # 3. Build page body and collect chart files to upload
        body_parts = [f"<p>Report generated on {timestamp}. Period: last {months} months.</p>\n"]
        charts_to_upload = []

        for chart_file, analysis_func, section_title in sections:
            chart_path = os.path.join(output_dir, chart_file)
            if not os.path.exists(chart_path):
                log(f"Skipping {chart_file} (not found)")
                continue

            charts_to_upload.append(chart_path)
            analysis_text = self._get_analysis_text(analysis_func, output_dir, months)
            body_parts.append(self._build_section_html(section_title, chart_file, analysis_text))

        body_html = "\n".join(body_parts)

        # Create the page with a placeholder, then upload attachments, then update body
        page_id = self._create_page(
            page_title,
            "<p>Uploading charts...</p>",
            parent_id=root_id,
        )
        log(f"Created report page (id={page_id})")

        # 4. Upload all chart attachments
        for chart_path in charts_to_upload:
            filename = os.path.basename(chart_path)
            log(f"Uploading {filename}...")
            self._upload_attachment(page_id, chart_path)

        # 5. Update page with final body referencing attachments
        self._update_page(page_id, page_title, body_html)
        log("Page updated with charts and analysis")

        page_url = f"{self.base_url}/wiki/spaces/{self.space_key}/pages/{page_id}"
        print(f"Confluence report published: {page_url}")
        return page_url
