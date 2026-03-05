# Plan: Add Team Member Weekly Throughput Chart

## Overview

Add a chart showing each team member's weekly throughput (issues completed) for the last 6 weeks. This helps visualize individual contributions and workload distribution.

## Data Available

From `issues_all.csv`:
- `assignee` - Team member name
- `done_week` - Week the issue was completed (YYYY-Www)

## Implementation

### New Chart: `chart_throughput_by_member.png`

**Type:** Grouped/stacked bar chart or heatmap
- **X-axis:** Week (last 6 weeks)
- **Y-axis:** Issues completed
- **Series:** One per team member (different colors)

### Options for Visualization

**Option A: Stacked Bar Chart**
- Each bar = one week
- Stacked segments = team members
- Shows total and individual contribution

**Option B: Grouped Bar Chart**
- Side-by-side bars for each team member per week
- Easier to compare individuals

**Option C: Heatmap**
- Rows = team members
- Columns = weeks
- Color intensity = issues completed

**Decision:** Option B (Grouped Bar) - user selected for easier individual comparison

## Implementation Steps

### Step 1: Add metric calculation in `jira_metrics.py`

Add `throughput_by_member` calculation in `calculate_metrics()`:
- Group completed issues by `done_week` and `assignee`
- Count issues per week per member

### Step 2: Add CSV export

Export `throughput_by_member.csv` with columns:
- `week`, `assignee`, `issues_completed`

### Step 3: Add chart generation in `charts.py`

Add `generate_throughput_by_member_chart()`:
- Filter to last 6 weeks
- Create stacked bar chart with team members as segments

## File Changes

| File | Change |
|------|--------|
| `jira_metrics.py` | Add metric calculation and CSV export |
| `charts.py` | Add `generate_throughput_by_member_chart()` |
