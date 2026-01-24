# JIRA Metrics Extractor

A CLI tool to extract metrics from JIRA Cloud for Kanban team reporting. Generates CSV reports and optional PNG charts for throughput, cycle time, workload, and more.

## Features

- **Throughput tracking** - Issues and story points completed per week
- **Cycle time analysis** - Time from In Progress to Done with weekly trends
- **WIP monitoring** - Current work in progress and aging items
- **Bug tracking** - Bugs created weekly by priority
- **Workload distribution** - Issues per assignee
- **Chart generation** - Optional PNG visualizations

## Installation

```bash
# Clone the repository
git clone https://github.com/hiepkhuc/jira-metrics.git
cd jira-metrics

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy the config template:
   ```bash
   cp config.py config_local.py
   ```

2. Edit `config_local.py` with your JIRA credentials:
   ```python
   JIRA_URL = "https://yourcompany.atlassian.net"
   JIRA_EMAIL = "your-email@example.com"
   JIRA_API_TOKEN = "your-api-token"
   ```

3. Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `JIRA_URL` | Your JIRA Cloud URL | - |
| `JIRA_EMAIL` | Your JIRA account email | - |
| `JIRA_API_TOKEN` | API token for authentication | - |
| `STORY_POINTS_FIELD` | Custom field ID for story points | `customfield_10016` |
| `IN_PROGRESS_STATUSES` | Statuses considered "in progress" | `["In Progress", "In Review", ...]` |
| `DONE_STATUSES` | Statuses considered "done" | `["Done", "Closed", ...]` |
| `AGING_WARNING_DAYS` | Days before WIP is flagged as warning | `14` |
| `AGING_CRITICAL_DAYS` | Days before WIP is flagged as critical | `30` |
| `OUTPUT_DIR` | Directory for output files | `output` |
| `DEFAULT_MONTHS` | Default months of data to extract | `6` |

## Usage

```bash
# Basic usage (extracts last 6 months)
python jira_metrics.py

# Extract last 3 months
python jira_metrics.py --months 3

# Generate charts along with CSVs
python jira_metrics.py --charts

# Custom output directory
python jira_metrics.py --output reports

# Verbose output
python jira_metrics.py -v

# Fetch all bug history for cumulative trend chart
python jira_metrics.py --charts --bug-history

# Combine options
python jira_metrics.py -m 3 -c -v -o reports
```

### CLI Options

| Option | Description |
|--------|-------------|
| `-m, --months` | Number of months to extract (default: from config) |
| `-c, --charts` | Generate PNG charts |
| `-o, --output` | Output directory |
| `-v, --verbose` | Enable verbose output |
| `--bug-history` | Fetch all bugs from beginning of time for cumulative trend |
| `-h, --help` | Show help message |

## Output Files

### CSV Reports

| File | Description |
|------|-------------|
| `issues_all.csv` | Raw issue data with all fields |
| `weekly_throughput.csv` | Issues and story points completed per week |
| `status_distribution.csv` | Count of issues by status |
| `assignee_workload.csv` | Current WIP per team member |
| `issue_types.csv` | Breakdown by issue type |
| `cycle_time_weekly.csv` | Cycle time statistics per week |
| `aging_wip.csv` | Items in progress too long |
| `bugs_created_weekly.csv` | Bugs created per week by priority |
| `bugs_cumulative.csv` | Cumulative bug trend (with `--bug-history`) |

### Charts (with `--charts` flag)

| File | Description |
|------|-------------|
| `chart_throughput.png` | Weekly throughput bar/line chart |
| `chart_cycle_time.png` | Cycle time trend with min/max range |
| `chart_status_distribution.png` | Status breakdown horizontal bars |
| `chart_issue_types.png` | Issue types donut chart |
| `chart_workload.png` | Assignee workload stacked bars |
| `chart_aging_wip.png` | Aging WIP colored by severity |
| `chart_bugs_created.png` | Bugs created weekly by priority |
| `chart_bugs_cumulative.png` | Cumulative bug trend (with `--bug-history`) |

## Example Output

### Weekly Throughput CSV
```csv
week,issues_completed,story_points_completed
2025-W48,12,45.5
2025-W49,8,32.0
2025-W50,15,58.0
```

### Bugs Created Weekly CSV
```csv
week,bugs_created,priority_critical,priority_high,priority_medium,priority_low
2025-W48,10,3,3,4,0
2025-W49,11,6,3,1,1
2025-W50,14,10,0,4,0
```

## Requirements

- Python 3.7+
- JIRA Cloud account with API access

### Dependencies

- `requests` - HTTP client for JIRA API
- `matplotlib` - Chart generation (optional, for `--charts`)
- `pandas` - Data manipulation (optional, for `--charts`)

## License

MIT
