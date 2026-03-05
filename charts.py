"""
Chart generation for JIRA metrics.

Generates PNG charts from the CSV files produced by jira_metrics.py.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


def parse_week(week_str: str) -> datetime:
    """Parse ISO week string (YYYY-Www) to datetime."""
    try:
        return datetime.strptime(week_str + "-1", "%Y-W%W-%w")
    except ValueError:
        return datetime.strptime(week_str + "-1", "%G-W%V-%u")


def generate_throughput_chart(output_dir: str, months: int = 6) -> None:
    """Generate weekly throughput chart with issues and story points."""
    csv_path = os.path.join(output_dir, "weekly_throughput.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)

    # Aggregate by date to handle overlapping weeks (e.g., 2025-W52 and 2026-W00)
    df = df.groupby("date", as_index=False)[["issues_completed", "story_points_completed"]].sum()
    df = df.sort_values("date")

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart for issues completed
    bars = ax1.bar(df["date"], df["issues_completed"], width=5, alpha=0.7,
                   color="#4CAF50", label="Issues Completed")
    ax1.set_xlabel("Week")
    ax1.set_ylabel("Issues Completed", color="#4CAF50")
    ax1.tick_params(axis="y", labelcolor="#4CAF50")

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, height + 0.5,
                     str(int(height)), ha="center", va="bottom", fontsize=8, color="#4CAF50")

    # Line chart for story points on secondary axis
    ax2 = ax1.twinx()
    line = ax2.plot(df["date"], df["story_points_completed"], color="#2196F3",
                    linewidth=2, marker="o", markersize=4, label="Story Points")
    ax2.set_ylabel("Story Points", color="#2196F3")
    ax2.tick_params(axis="y", labelcolor="#2196F3")

    # Add value labels for story points
    for date, points in zip(df["date"], df["story_points_completed"]):
        if points > 0:
            ax2.text(date, points + 2, str(int(points)), ha="center", va="bottom",
                     fontsize=8, color="#2196F3")

    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-W%W"))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=max(1, len(df) // 10)))
    plt.xticks(rotation=45, ha="right")

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.title(f"Weekly Team Throughput (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_throughput.png"), dpi=150)
    plt.close()


def generate_cycle_time_chart(output_dir: str, months: int = 6) -> None:
    """Generate cycle time trend chart with min/max range."""
    csv_path = os.path.join(output_dir, "cycle_time_weekly.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)
    df = df.sort_values("date")

    # Filter to last N months
    cutoff_date = datetime.now() - pd.Timedelta(days=months * 30)
    df = df[df["date"] >= cutoff_date]

    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # Shaded area for min/max range
    ax.fill_between(df["date"], df["min_cycle_time_days"], df["max_cycle_time_days"],
                    alpha=0.2, color="#FF9800", label="Min-Max Range")

    # Line for average
    ax.plot(df["date"], df["avg_cycle_time_days"], color="#FF5722",
            linewidth=2, marker="o", markersize=4, label="Average")

    # Line for median
    ax.plot(df["date"], df["median_cycle_time_days"], color="#9C27B0",
            linewidth=2, marker="s", markersize=4, linestyle="--", label="Median")

    # Add value labels for average and median
    for date, avg, median in zip(df["date"], df["avg_cycle_time_days"], df["median_cycle_time_days"]):
        ax.text(date, avg + 2, f"{avg:.1f}", ha="center", va="bottom", fontsize=7, color="#FF5722")
        ax.text(date, median - 2, f"{int(median)}", ha="center", va="top", fontsize=7, color="#9C27B0")

    ax.set_xlabel("Week")
    ax.set_ylabel("Cycle Time (Days)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-W%W"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=max(1, len(df) // 10)))
    plt.xticks(rotation=45, ha="right")

    ax.legend(loc="upper right")
    ax.set_ylim(bottom=0)

    plt.title(f"Cycle Time Trend (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_cycle_time.png"), dpi=150)
    plt.close()


def generate_lead_time_chart(output_dir: str, months: int = 6) -> None:
    """Generate lead time trend chart with min/max range."""
    csv_path = os.path.join(output_dir, "lead_time_weekly.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)
    df = df.sort_values("date")

    # Filter to last N months
    cutoff_date = datetime.now() - pd.Timedelta(days=months * 30)
    df = df[df["date"] >= cutoff_date]

    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # Shaded area for min/max range
    ax.fill_between(df["date"], df["min_lead_time_days"], df["max_lead_time_days"],
                    alpha=0.2, color="#2196F3", label="Min-Max Range")

    # Line for average
    ax.plot(df["date"], df["avg_lead_time_days"], color="#1976D2",
            linewidth=2, marker="o", markersize=4, label="Average")

    # Line for median
    ax.plot(df["date"], df["median_lead_time_days"], color="#7B1FA2",
            linewidth=2, marker="s", markersize=4, linestyle="--", label="Median")

    # Add value labels for average and median
    for date, avg, median in zip(df["date"], df["avg_lead_time_days"], df["median_lead_time_days"]):
        ax.text(date, avg + 2, f"{avg:.1f}", ha="center", va="bottom", fontsize=7, color="#1976D2")
        ax.text(date, median - 2, f"{int(median)}", ha="center", va="top", fontsize=7, color="#7B1FA2")

    ax.set_xlabel("Week")
    ax.set_ylabel("Lead Time (Days)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-W%W"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=max(1, len(df) // 10)))
    plt.xticks(rotation=45, ha="right")

    ax.legend(loc="upper right")
    ax.set_ylim(bottom=0)

    plt.title(f"Lead Time Trend (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_lead_time.png"), dpi=150)
    plt.close()


def generate_status_distribution_chart(output_dir: str, months: int = 6) -> None:
    """Generate horizontal bar chart for status distribution."""
    csv_path = os.path.join(output_dir, "status_distribution.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Sort by count ascending for horizontal bar (top = highest)
    df = df.sort_values("count", ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))

    colors = plt.cm.viridis(df["count"] / df["count"].max())
    bars = ax.barh(df["status"], df["count"], color=colors)

    # Add value labels
    for bar, count in zip(bars, df["count"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", fontsize=9)

    ax.set_xlabel("Number of Issues")
    ax.set_ylabel("Status")
    ax.set_xlim(right=df["count"].max() * 1.1)

    plt.title(f"Status Distribution (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_status_distribution.png"), dpi=150)
    plt.close()


def generate_issue_types_chart(output_dir: str, months: int = 6) -> None:
    """Generate pie/donut chart for issue types."""
    csv_path = os.path.join(output_dir, "issue_types.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 8))

    colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"]
    wedges, texts, autotexts = ax.pie(
        df["count"],
        labels=df["issue_type"],
        autopct=lambda pct: f"{pct:.1f}%\n({int(pct/100*df['count'].sum())})",
        colors=colors[:len(df)],
        wedgeprops=dict(width=0.6),  # Donut style
        pctdistance=0.75,
    )

    for autotext in autotexts:
        autotext.set_fontsize(9)

    plt.title(f"Issue Types Distribution (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_issue_types.png"), dpi=150)
    plt.close()


def generate_workload_chart(output_dir: str, weeks: int = 6) -> None:
    """Generate stacked horizontal bar chart for assignee workload."""
    csv_path = os.path.join(output_dir, "assignee_workload.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Ensure columns exist
    for col in ["to_do", "in_progress", "done"]:
        if col not in df.columns:
            df[col] = 0

    df["total"] = df["to_do"] + df["in_progress"] + df["done"]

    # Sort by total ascending (for horizontal bar, top = highest)
    df = df.sort_values("total", ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))

    # Stacked horizontal bars: To Do, In Progress, Done
    bars_todo = ax.barh(df["assignee"], df["to_do"], color="#FF9800", label="To Do")
    bars_wip = ax.barh(df["assignee"], df["in_progress"], left=df["to_do"],
                       color="#F44336", label="In Progress")
    bars_done = ax.barh(df["assignee"], df["done"],
                        left=df["to_do"] + df["in_progress"],
                        color="#4CAF50", label="Done")

    # Add value labels
    for bar_todo, bar_wip, bar_done, todo, wip, done, total in zip(
            bars_todo, bars_wip, bars_done,
            df["to_do"], df["in_progress"], df["done"], df["total"]):
        if todo > 0:
            ax.text(todo / 2, bar_todo.get_y() + bar_todo.get_height() / 2,
                    str(int(todo)), ha="center", va="center", fontsize=9,
                    color="white", fontweight="bold")
        if wip > 0:
            ax.text(todo + wip / 2, bar_wip.get_y() + bar_wip.get_height() / 2,
                    str(int(wip)), ha="center", va="center", fontsize=9,
                    color="white", fontweight="bold")
        if done > 0:
            ax.text(todo + wip + done / 2, bar_done.get_y() + bar_done.get_height() / 2,
                    str(int(done)), ha="center", va="center", fontsize=9,
                    color="white", fontweight="bold")
        # Total label at the end
        ax.text(total + 0.3, bar_todo.get_y() + bar_todo.get_height() / 2,
                str(int(total)), ha="left", va="center", fontsize=9, color="#333")

    ax.set_xlabel("Number of Issues")
    ax.set_ylabel("Assignee")
    ax.legend(loc="lower right")
    ax.set_xlim(right=df["total"].max() * 1.15)

    plt.title("Assignee Workload (Period: Last 3 Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_workload.png"), dpi=150)
    plt.close()


def generate_aging_wip_chart(output_dir: str, months: int = 6) -> None:
    """Generate horizontal bar chart for aging WIP colored by severity."""
    csv_path = os.path.join(output_dir, "aging_wip.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Take top 20 oldest items
    df = df.head(20)
    df = df.sort_values("aging_days", ascending=True)

    # Create labels with key and truncated summary
    df["label"] = df.apply(
        lambda r: f"{r['key']}: {r['summary'][:30]}..." if len(r['summary']) > 30
        else f"{r['key']}: {r['summary']}",
        axis=1
    )

    fig, ax = plt.subplots(figsize=(12, max(6, len(df) * 0.4)))

    # Color by severity
    color_map = {"CRITICAL": "#F44336", "WARNING": "#FF9800", "OK": "#4CAF50"}
    colors = [color_map.get(s, "#BDBDBD") for s in df["severity"]]

    bars = ax.barh(df["label"], df["aging_days"], color=colors)

    # Add value labels
    for bar, days in zip(bars, df["aging_days"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{days}d", va="center", fontsize=9)

    ax.set_xlabel("Days in Progress")
    ax.set_ylabel("Issue")
    ax.set_xlim(right=df["aging_days"].max() * 1.15)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#F44336", label="Critical (30+ days)"),
        Patch(facecolor="#FF9800", label="Warning (14-29 days)"),
        Patch(facecolor="#4CAF50", label="OK (<14 days)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    plt.title(f"Aging Work In Progress - Top 20 (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_aging_wip.png"), dpi=150)
    plt.close()


def generate_bugs_created_chart(output_dir: str, months: int = 6) -> None:
    """Generate stacked bar chart for bugs created weekly by priority."""
    csv_path = os.path.join(output_dir, "bugs_created_weekly.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)

    # Aggregate by date to handle overlapping weeks (e.g., 2025-W52 and 2026-W00)
    priority_cols = [c for c in df.columns if c.startswith("priority_")]
    df = df.groupby("date", as_index=False)[priority_cols + ["bugs_created"]].sum()
    df = df.sort_values("date")

    # Filter to last N months
    cutoff_date = datetime.now() - pd.Timedelta(days=months * 30)
    df = df[df["date"] >= cutoff_date]

    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # Stacked bar chart by priority
    bar_width = 5
    bottom = [0] * len(df)

    priority_colors = [
        ("priority_critical", "#B71C1C", "Critical"),
        ("priority_highest", "#F44336", "Highest"),
        ("priority_high", "#FF9800", "High"),
        ("priority_medium", "#FFC107", "Medium"),
        ("priority_low", "#4CAF50", "Low"),
    ]

    for col, color, label in priority_colors:
        if col in df.columns:
            ax.bar(df["date"], df[col], width=bar_width, bottom=bottom,
                   color=color, label=label, alpha=0.9)
            bottom = [b + v for b, v in zip(bottom, df[col])]

    # Add total count labels on top of bars
    for i, (date, total) in enumerate(zip(df["date"], bottom)):
        if total > 0:
            ax.text(date, total + 0.3, str(int(total)), ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Week")
    ax.set_ylabel("Bugs Created")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-W%W"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=max(1, len(df) // 10)))
    plt.xticks(rotation=45, ha="right")

    ax.legend(loc="upper right")
    ax.set_ylim(bottom=0)

    plt.title(f"Bugs Created Weekly by Priority (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_bugs_created.png"), dpi=150)
    plt.close()


def generate_correction_required_chart(output_dir: str, months: int = 6) -> None:
    """Generate bar chart for tickets moved to 'Correction Required' weekly."""
    csv_path = os.path.join(output_dir, "correction_required_weekly.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)
    df = df.sort_values("date")

    # Filter to last N months
    cutoff_date = datetime.now() - pd.Timedelta(days=months * 30)
    df = df[df["date"] >= cutoff_date]

    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # Bar chart
    bars = ax.bar(df["date"], df["count"], width=5, alpha=0.8, color="#FF5722")

    # Add trend line
    if len(df) > 1:
        z = np.polyfit(range(len(df)), df["count"], 1)
        p = np.poly1d(z)
        ax.plot(df["date"], p(range(len(df))), color="#B71C1C",
                linewidth=2, linestyle="--", label="Trend")
        ax.legend(loc="upper left")

    ax.set_xlabel("Week")
    ax.set_ylabel("Tickets Moved to Correction Required")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-W%W"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=max(1, len(df) // 10)))
    plt.xticks(rotation=45, ha="right")

    ax.set_ylim(bottom=0)

    plt.title(f"Weekly Tickets Moved to 'Correction Required' (Last {months} Months)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_correction_required.png"), dpi=150)
    plt.close()


def generate_throughput_by_member_chart(output_dir: str, weeks: int = 6) -> None:
    """Generate grouped bar chart showing each team member's weekly throughput."""
    csv_path = os.path.join(output_dir, "throughput_by_member.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)

    # Get last N weeks
    all_weeks = sorted(df["week"].unique())
    recent_weeks = all_weeks[-weeks:] if len(all_weeks) >= weeks else all_weeks
    df = df[df["week"].isin(recent_weeks)]

    if df.empty:
        return

    # Pivot to get members as columns
    pivot_df = df.pivot_table(
        index="week", columns="assignee", values="issues_completed", fill_value=0
    )

    # Sort weeks chronologically
    pivot_df = pivot_df.reindex(sorted(pivot_df.index, key=lambda w: parse_week(w)))

    # Get top contributors (by total) to limit legend size
    totals = pivot_df.sum().sort_values(ascending=False)
    top_members = totals.head(10).index.tolist()
    pivot_df = pivot_df[top_members]

    fig, ax = plt.subplots(figsize=(14, 7))

    # Create grouped bar chart
    x = range(len(pivot_df.index))
    width = 0.8 / len(pivot_df.columns)
    colors = plt.cm.tab10(range(len(pivot_df.columns)))

    for i, (member, color) in enumerate(zip(pivot_df.columns, colors)):
        offset = (i - len(pivot_df.columns) / 2 + 0.5) * width
        bars = ax.bar([xi + offset for xi in x], pivot_df[member],
                      width=width, label=member, color=color, alpha=0.8)
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1,
                        str(int(height)), ha="center", va="bottom", fontsize=7)

    ax.set_xlabel("Week")
    ax.set_ylabel("Issues Completed")
    ax.set_xticks(x)
    ax.set_xticklabels(pivot_df.index, rotation=45, ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=9)
    ax.set_ylim(bottom=0)

    plt.title(f"Team Member Throughput (Last {len(pivot_df)} Weeks)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_throughput_by_member.png"), dpi=150)
    plt.close()


def generate_wip_health_chart(output_dir: str, months: int = 6) -> None:
    """Generate WIP Health table showing assignees by WIP status."""
    csv_path = os.path.join(output_dir, "wip_health.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Filter to assignees with WIP items, sort by total descending
    df = df[df["Total"] > 0].sort_values("Total", ascending=False).reset_index(drop=True)
    if df.empty:
        return

    # Create table-style heatmap using matplotlib
    # Dynamically detect status columns from CSV (all columns except "assignee" and "Total")
    status_cols = [c for c in df.columns if c not in ("assignee", "Total")]
    col_labels = [c.replace("_", "\n") for c in status_cols] + ["Total"]

    n_rows = len(df) + 1  # +1 for totals row
    n_cols = len(status_cols) + 1  # +1 for totals column
    cell_width = 1.8  # Width of each cell
    cell_height = 0.8  # Height of each cell

    fig_width = n_cols * cell_width + 3  # Extra space for row labels
    fig_height = max(4, (n_rows + 1) * cell_height + 1.5)  # +1 for header row
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Create data matrix for heatmap
    data = df[status_cols].values

    # Calculate max value for color scaling
    max_val = data.max() if data.max() > 0 else 1
    cmap = plt.cm.Blues

    # Draw assignee rows (starting from row 1, row 0 is for totals)
    for i, assignee in enumerate(df["assignee"]):
        row_y = (len(df) - i) * cell_height  # Start from top, leave row 0 for totals

        for j, col in enumerate(status_cols):
            val = df.iloc[i][col]
            color = cmap(val / max_val * 0.7) if val > 0 else "white"
            rect = plt.Rectangle((j * cell_width, row_y), cell_width, cell_height,
                                 facecolor=color, edgecolor="gray", linewidth=0.5)
            ax.add_patch(rect)
            ax.text(j * cell_width + cell_width / 2, row_y + cell_height / 2, str(int(val)),
                   ha="center", va="center", fontsize=10, fontweight="bold",
                   color="#1565C0" if val > 0 else "gray")

        # Total column for this row
        total = df.iloc[i]["Total"]
        rect = plt.Rectangle((len(status_cols) * cell_width, row_y), cell_width, cell_height,
                             facecolor="#E3F2FD", edgecolor="gray", linewidth=0.5)
        ax.add_patch(rect)
        ax.text(len(status_cols) * cell_width + cell_width / 2, row_y + cell_height / 2, str(int(total)),
               ha="center", va="center", fontsize=10, fontweight="bold", color="#1565C0")

        # Row label (assignee name) - draw to the left
        ax.text(-0.2, row_y + cell_height / 2, assignee,
               ha="right", va="center", fontsize=10)

    # Add column totals row at bottom (row 0)
    col_totals = df[status_cols].sum()
    grand_total = df["Total"].sum()
    totals_row_y = 0

    for j, col in enumerate(status_cols):
        rect = plt.Rectangle((j * cell_width, totals_row_y), cell_width, cell_height,
                             facecolor="#E8E8E8", edgecolor="gray", linewidth=0.5)
        ax.add_patch(rect)
        ax.text(j * cell_width + cell_width / 2, totals_row_y + cell_height / 2, str(int(col_totals[col])),
               ha="center", va="center", fontsize=10, fontweight="bold", color="#1565C0")

    # Grand total cell
    rect = plt.Rectangle((len(status_cols) * cell_width, totals_row_y), cell_width, cell_height,
                         facecolor="#BBDEFB", edgecolor="gray", linewidth=0.5)
    ax.add_patch(rect)
    ax.text(len(status_cols) * cell_width + cell_width / 2, totals_row_y + cell_height / 2, str(int(grand_total)),
           ha="center", va="center", fontsize=11, fontweight="bold", color="#1565C0")

    # "Total" row label
    ax.text(-0.2, totals_row_y + cell_height / 2, "Total",
           ha="right", va="center", fontsize=10, fontweight="bold")

    # Draw column headers at top
    header_y = (len(df) + 1) * cell_height
    for j, label in enumerate(col_labels):
        ax.text(j * cell_width + cell_width / 2, header_y + 0.2, label,
               ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Configure axes
    ax.set_xlim(-0.3, n_cols * cell_width)
    ax.set_ylim(-0.1, header_y + cell_height)

    # Hide axes but keep the figure
    ax.axis("off")

    plt.title(f"WIP Health by Assignee (Last {months} Months)", fontsize=12, fontweight="bold", pad=30)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_wip_health.png"), dpi=150, bbox_inches="tight")
    plt.close()


def generate_bugs_cumulative_chart(output_dir: str) -> None:
    """Generate cumulative bug trend chart showing created, resolved, and open bugs."""
    csv_path = os.path.join(output_dir, "bugs_cumulative.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)
    df = df.sort_values("date")

    fig, ax = plt.subplots(figsize=(14, 7))

    # Fill area for resolved bugs (green)
    ax.fill_between(df["date"], 0, df["cumulative_resolved"],
                    alpha=0.3, color="#4CAF50", label="Resolved (cumulative)")

    # Line for cumulative created (red)
    ax.plot(df["date"], df["cumulative_created"], color="#F44336",
            linewidth=2, label="Created (cumulative)")

    # Line for open bugs (blue, dashed)
    ax.plot(df["date"], df["open_bugs"], color="#2196F3",
            linewidth=2.5, linestyle="-", label="Open Bugs (remaining)")

    ax.set_xlabel("Time")
    ax.set_ylabel("Bug Count")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(df) // 20)))
    plt.xticks(rotation=45, ha="right")

    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)

    # Add summary text box with latest values
    latest = df.iloc[-1]
    summary_text = (
        f"Latest Summary:\n"
        f"  Created: {int(latest['cumulative_created'])}\n"
        f"  Resolved: {int(latest['cumulative_resolved'])}\n"
        f"  Open: {int(latest['open_bugs'])}"
    )
    ax.text(0.02, 0.58, summary_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'))
    ax.legend(loc="upper left")

    plt.title("Cumulative Bug Trend (All Time)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_bugs_cumulative.png"), dpi=150)
    plt.close()


# =============================================================================
# Analysis Functions
# =============================================================================


def analyze_throughput(output_dir: str, months: int) -> str:
    """Analyze throughput data and return insights."""
    csv_path = os.path.join(output_dir, "weekly_throughput.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    avg_issues = df["issues_completed"].mean()
    avg_points = df["story_points_completed"].mean()
    recent_weeks = df.tail(4)
    recent_avg = recent_weeks["issues_completed"].mean()

    min_issues = df["issues_completed"].min()
    max_issues = df["issues_completed"].max()
    min_week = df.loc[df["issues_completed"].idxmin(), "week"]
    max_week = df.loc[df["issues_completed"].idxmax(), "week"]
    variance = df["issues_completed"].std()

    trend = "increasing" if recent_avg > avg_issues * 1.1 else "decreasing" if recent_avg < avg_issues * 0.9 else "stable"

    lines = [
        "THROUGHPUT",
        "-" * 40,
        f"Average weekly throughput: {avg_issues:.1f} issues ({avg_points:.1f} story points).",
        f"Recent 4-week average is {recent_avg:.1f} issues, showing a {trend} trend compared to overall.",
        f"Peak week: {max_week} with {max_issues} issues. Lowest week: {min_week} with {min_issues} issues.",
    ]

    # High variance warning
    if variance > avg_issues * 0.5:
        lines.append(f"⚠️ High variance detected ({min_issues}-{max_issues} range) - investigate causes of low-output weeks.")

    # Decreasing trend warning
    if trend == "decreasing":
        lines.append("⚠️ Throughput is declining - review blockers or capacity issues affecting recent sprints.")

    # Recommendation
    if variance > avg_issues * 0.5 or trend == "decreasing":
        lines.append("Consider: Conduct retrospective on low-output weeks to identify and address recurring blockers.")

    lines.append("")
    return "\n".join(lines)


def analyze_cycle_time(output_dir: str, months: int) -> str:
    """Analyze cycle time data and return insights."""
    csv_path = os.path.join(output_dir, "cycle_time_weekly.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    avg_cycle = df["avg_cycle_time_days"].mean()
    median_cycle = df["median_cycle_time_days"].mean()
    recent = df.tail(4)["avg_cycle_time_days"].mean()
    min_cycle = df["avg_cycle_time_days"].min()
    max_cycle = df["avg_cycle_time_days"].max()

    trend = "improving" if recent < avg_cycle * 0.9 else "worsening" if recent > avg_cycle * 1.1 else "stable"

    lines = [
        "CYCLE TIME",
        "-" * 40,
        f"Average cycle time: {avg_cycle:.1f} days (median: {median_cycle:.1f} days).",
        f"Recent trend is {trend} with last 4 weeks averaging {recent:.1f} days.",
        f"Range: {min_cycle:.1f} to {max_cycle:.1f} days across all weeks.",
    ]

    # Outlier warning (avg >> median indicates outliers skewing the data)
    if avg_cycle > median_cycle * 1.5:
        lines.append(f"⚠️ Average significantly exceeds median - outliers are skewing cycle time upward.")
        lines.append("Consider: Investigate long-running tickets causing cycle time spikes.")

    # Worsening trend warning
    if trend == "worsening":
        lines.append("⚠️ Cycle time is increasing - work is taking longer to complete.")
        lines.append("Consider: Review process bottlenecks and blocked items to improve flow.")

    # High variability warning
    if max_cycle > avg_cycle * 2:
        lines.append(f"⚠️ High variability detected (max {max_cycle:.1f} days vs avg {avg_cycle:.1f} days).")

    lines.append("")
    return "\n".join(lines)


def analyze_lead_time(output_dir: str, months: int) -> str:
    """Analyze lead time data and return insights."""
    csv_path = os.path.join(output_dir, "lead_time_weekly.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    avg_lead = df["avg_lead_time_days"].mean()
    median_lead = df["median_lead_time_days"].mean()
    recent = df.tail(4)["avg_lead_time_days"].mean()
    min_lead = df["avg_lead_time_days"].min()
    max_lead = df["avg_lead_time_days"].max()

    trend = "improving" if recent < avg_lead * 0.9 else "worsening" if recent > avg_lead * 1.1 else "stable"

    # Try to calculate cycle-to-lead gap
    cycle_path = os.path.join(output_dir, "cycle_time_weekly.csv")
    cycle_gap_msg = ""
    if os.path.exists(cycle_path):
        cycle_df = pd.read_csv(cycle_path)
        if not cycle_df.empty:
            avg_cycle = cycle_df["avg_cycle_time_days"].mean()
            wait_time = avg_lead - avg_cycle
            if wait_time > 0:
                cycle_gap_msg = f"Average wait time before work starts: {wait_time:.1f} days (lead - cycle)."

    lines = [
        "LEAD TIME",
        "-" * 40,
        f"Average lead time: {avg_lead:.1f} days (median: {median_lead:.1f} days).",
        f"Recent trend is {trend} with last 4 weeks averaging {recent:.1f} days.",
    ]

    if cycle_gap_msg:
        lines.append(cycle_gap_msg)

    # Outlier warning
    if avg_lead > median_lead * 1.5:
        lines.append(f"⚠️ Average significantly exceeds median - some items have very long lead times.")

    # Worsening trend warning
    if trend == "worsening":
        lines.append("⚠️ Lead time is increasing - items are taking longer from creation to completion.")

    # High lead time warning
    if avg_lead > 30:
        lines.append("⚠️ High lead time (>30 days) - consider breaking work into smaller items.")
        lines.append("Consider: Review backlog prioritization to reduce time items wait before starting.")

    lines.append("")
    return "\n".join(lines)


def analyze_status_distribution(output_dir: str, months: int) -> str:
    """Analyze status distribution and return insights."""
    csv_path = os.path.join(output_dir, "status_distribution.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    total = df["count"].sum()
    wip_statuses = ["In Progress", "In Review", "In QA", "Correction Required"]
    wip_df = df[df["status"].isin(wip_statuses)]
    wip_count = wip_df["count"].sum()
    top_status = df.loc[df["count"].idxmax()]

    # Find bottleneck status (highest WIP count that isn't "In Progress")
    review_statuses = ["In Review", "In QA", "Correction Required", "Awaiting Feedback"]
    review_df = df[df["status"].isin(review_statuses)]

    lines = [
        "STATUS DISTRIBUTION",
        "-" * 40,
        f"Total {total} issues across all statuses, with {wip_count} currently in WIP states.",
        f"Largest category: '{top_status['status']}' with {top_status['count']} issues ({top_status['count']/total*100:.1f}%).",
    ]

    # WIP ratio warning
    wip_ratio = wip_count / total * 100 if total > 0 else 0
    if wip_ratio > 30:
        lines.append(f"⚠️ High WIP ratio ({wip_ratio:.1f}%) - too much work in progress may reduce focus.")

    # Bottleneck detection
    if not review_df.empty:
        bottleneck = review_df.loc[review_df["count"].idxmax()]
        if bottleneck["count"] > wip_count * 0.4:
            lines.append(f"⚠️ Bottleneck detected: '{bottleneck['status']}' has {bottleneck['count']} items ({bottleneck['count']/wip_count*100:.1f}% of WIP).")
            lines.append("Consider: Add capacity to this stage or investigate why items are stuck here.")

    # Correction Required warning
    correction = df[df["status"] == "Correction Required"]
    if not correction.empty and correction.iloc[0]["count"] > 5:
        lines.append(f"⚠️ {correction.iloc[0]['count']} items need corrections - potential quality concern.")

    lines.append("")
    return "\n".join(lines)


def analyze_issue_types(output_dir: str, months: int) -> str:
    """Analyze issue types and return insights."""
    csv_path = os.path.join(output_dir, "issue_types.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    total = df["count"].sum()
    bug_count = df[df["issue_type"].str.lower() == "bug"]["count"].sum()
    bug_ratio = bug_count / total * 100 if total > 0 else 0
    top_type = df.loc[df["count"].idxmax()]

    # Calculate feature vs maintenance ratio
    feature_types = ["Story", "Task", "Feature", "Epic"]
    maintenance_types = ["Bug", "Sub-task", "Technical Debt"]
    feature_count = df[df["issue_type"].isin(feature_types)]["count"].sum()
    maintenance_count = df[df["issue_type"].str.lower().isin([t.lower() for t in maintenance_types])]["count"].sum()

    lines = [
        "ISSUE TYPES",
        "-" * 40,
        f"Bug ratio: {bug_ratio:.1f}% ({bug_count} of {total} issues).",
        f"Most common type: '{top_type['issue_type']}' accounting for {top_type['count']/total*100:.1f}% of all issues.",
    ]

    if feature_count > 0 and maintenance_count > 0:
        lines.append(f"Feature work: {feature_count} items vs maintenance/bugs: {maintenance_count} items.")

    # High bug ratio warning
    if bug_ratio > 40:
        lines.append(f"⚠️ High bug ratio ({bug_ratio:.1f}%) - more than 40% of work is bug fixes.")
        lines.append("Consider: Invest in testing, code reviews, or technical debt reduction.")
    elif bug_ratio > 25:
        lines.append(f"⚠️ Elevated bug ratio ({bug_ratio:.1f}%) - consider preventive quality measures.")

    # Priority imbalance - check if priority data is available in another file
    priority_path = os.path.join(output_dir, "issue_priority.csv")
    if os.path.exists(priority_path):
        prio_df = pd.read_csv(priority_path)
        if not prio_df.empty:
            high_prio = prio_df[prio_df["priority"].str.lower().isin(["critical", "highest", "high"])]["count"].sum()
            high_ratio = high_prio / prio_df["count"].sum() * 100 if prio_df["count"].sum() > 0 else 0
            if high_ratio > 50:
                lines.append(f"⚠️ Priority imbalance: {high_ratio:.1f}% of issues are high priority or above.")

    lines.append("")
    return "\n".join(lines)


def analyze_workload(output_dir: str, weeks: int = 6) -> str:
    """Analyze assignee workload and return insights."""
    csv_path = os.path.join(output_dir, "assignee_workload.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    # Ensure columns exist
    for col in ["to_do", "in_progress", "done"]:
        if col not in df.columns:
            df[col] = 0

    total_todo = df["to_do"].sum()
    total_wip = df["in_progress"].sum()
    total_done = df["done"].sum()
    top_loaded = df.nlargest(3, "in_progress")
    top_names = ", ".join(f"{r['assignee']} ({r['in_progress']})" for _, r in top_loaded.iterrows())
    avg_wip = df["in_progress"].mean()
    max_wip = df["in_progress"].max()
    min_wip = df["in_progress"].min()
    std_wip = df["in_progress"].std()

    lines = [
        "WORKLOAD",
        "-" * 40,
        f"To Do: {total_todo}, In Progress: {total_wip}, Done: {total_done}.",
        f"Average WIP per person: {avg_wip:.1f} issues.",
        f"Top loaded: {top_names}.",
        f"WIP range: {min_wip} to {max_wip} items per person.",
    ]

    # Overloaded member warning
    overloaded = df[df["in_progress"] > avg_wip * 2]
    if not overloaded.empty:
        overloaded_names = ", ".join(overloaded["assignee"].tolist())
        lines.append(f"⚠️ Overloaded team members (>2x avg): {overloaded_names}.")
        lines.append("Consider: Redistribute work or add capacity to prevent burnout.")

    # Workload imbalance warning
    if std_wip > avg_wip * 0.8 and len(df) > 2:
        lines.append("⚠️ High workload imbalance - WIP distribution is uneven across team.")

    # High individual WIP warning
    if max_wip > 5:
        high_wip_member = df.loc[df["in_progress"].idxmax(), "assignee"]
        lines.append(f"⚠️ {high_wip_member} has {max_wip} items in progress - consider WIP limits.")

    # Members with only To Do items (no WIP)
    todo_only = df[(df["in_progress"] == 0) & (df["to_do"] > 0)]
    if not todo_only.empty:
        todo_names = ", ".join(todo_only["assignee"].tolist())
        lines.append(f"Action: {todo_names} have To Do items but nothing in progress - consider starting work.")

    lines.append("")
    return "\n".join(lines)


def analyze_aging_wip(output_dir: str, months: int) -> str:
    """Analyze aging WIP and return insights."""
    csv_path = os.path.join(output_dir, "aging_wip.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    total = len(df)
    critical_df = df[df["severity"] == "CRITICAL"]
    warning_df = df[df["severity"] == "WARNING"]
    critical = len(critical_df)
    warning = len(warning_df)
    avg_age = df["aging_days"].mean()
    max_age = df["aging_days"].max()

    lines = [
        "AGING WIP",
        "-" * 40,
        f"{total} items in WIP with average age of {avg_age:.1f} days.",
        f"Risk breakdown: {critical} critical (30+ days), {warning} warning (14-29 days).",
    ]

    # List critical items by name (top 3)
    if critical > 0:
        critical_items = critical_df.nlargest(3, "aging_days")
        critical_list = ", ".join(
            f"{r['key']} ({r['aging_days']}d)" for _, r in critical_items.iterrows()
        )
        lines.append(f"⚠️ Critical aging items: {critical_list}.")
        lines.append("Action: Prioritize unblocking these items or consider closing/canceling if stale.")

    # Warning about stale items
    if critical > 3:
        lines.append(f"⚠️ {critical} items over 30 days old - significant risk of becoming obsolete.")

    # Oldest item warning
    if max_age > 60:
        oldest = df.loc[df["aging_days"].idxmax()]
        lines.append(f"⚠️ Oldest item: {oldest['key']} at {max_age} days - review if still relevant.")

    # High average age warning
    if avg_age > 14:
        lines.append("⚠️ Average WIP age exceeds 2 weeks - work is staying in progress too long.")
        lines.append("Consider: Implement WIP limits and focus on completing started work before starting new.")

    lines.append("")
    return "\n".join(lines)


def analyze_bugs_created(output_dir: str, months: int) -> str:
    """Analyze bugs created and return insights."""
    csv_path = os.path.join(output_dir, "bugs_created_weekly.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    total_bugs = df["bugs_created"].sum()
    avg_weekly = df["bugs_created"].mean()
    recent = df.tail(4)["bugs_created"].mean()
    max_weekly = df["bugs_created"].max()
    max_week = df.loc[df["bugs_created"].idxmax(), "week"]

    priority_cols = [c for c in df.columns if c.startswith("priority_")]
    priority_totals = {c.replace("priority_", ""): df[c].sum() for c in priority_cols}
    top_priority = max(priority_totals, key=priority_totals.get) if priority_totals else "N/A"

    # Count high-priority bugs
    high_priority_count = sum(
        priority_totals.get(p, 0) for p in ["critical", "highest", "high"]
    )
    high_priority_ratio = high_priority_count / total_bugs * 100 if total_bugs > 0 else 0

    trend = "increasing" if recent > avg_weekly * 1.1 else "decreasing" if recent < avg_weekly * 0.9 else "stable"

    lines = [
        "BUGS CREATED",
        "-" * 40,
        f"Total {total_bugs} bugs created, averaging {avg_weekly:.1f} per week ({trend} trend recently).",
        f"Most common priority: {top_priority} ({priority_totals.get(top_priority, 0)} bugs).",
        f"Peak week: {max_week} with {max_weekly} bugs. High priority bugs: {high_priority_count} ({high_priority_ratio:.1f}%).",
    ]

    # Increasing trend warning
    if trend == "increasing":
        lines.append("⚠️ Bug creation rate is increasing - quality may be declining.")
        lines.append("Consider: Review recent releases for root causes and improve testing coverage.")

    # High priority bug warning
    if high_priority_ratio > 30:
        lines.append(f"⚠️ High ratio of critical/high priority bugs ({high_priority_ratio:.1f}%) - severe issues being found.")

    # Spike detection
    if max_weekly > avg_weekly * 2:
        lines.append(f"⚠️ Bug spike detected in {max_week} ({max_weekly} bugs vs {avg_weekly:.1f} avg).")
        lines.append("Action: Investigate what release or change caused the spike.")

    lines.append("")
    return "\n".join(lines)


def analyze_correction_required(output_dir: str, months: int) -> str:
    """Analyze correction required trend and return insights."""
    csv_path = os.path.join(output_dir, "correction_required_weekly.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    total = df["count"].sum()
    avg_weekly = df["count"].mean()
    recent = df.tail(4)["count"].mean()
    max_weekly = df["count"].max()
    max_week = df.loc[df["count"].idxmax(), "week"]

    # Calculate weeks with corrections
    weeks_with_corrections = len(df[df["count"] > 0])
    total_weeks = len(df)
    correction_frequency = weeks_with_corrections / total_weeks * 100 if total_weeks > 0 else 0

    trend = "increasing" if recent > avg_weekly * 1.1 else "decreasing" if recent < avg_weekly * 0.9 else "stable"

    lines = [
        "CORRECTION REQUIRED",
        "-" * 40,
        f"Total {total} items moved to 'Correction Required', averaging {avg_weekly:.1f} per week.",
        f"Recent trend is {trend} with last 4 weeks averaging {recent:.1f} per week.",
        f"Corrections occurred in {weeks_with_corrections} of {total_weeks} weeks ({correction_frequency:.1f}%).",
    ]

    # Increasing trend warning (quality concern)
    if trend == "increasing":
        lines.append("⚠️ Increasing correction rate - code quality or review process may need attention.")
        lines.append("Consider: Strengthen code review standards and add pre-commit checks.")

    # High correction rate warning
    if avg_weekly > 3:
        lines.append(f"⚠️ High correction rate ({avg_weekly:.1f}/week) - indicates systematic quality issues.")

    # Spike detection
    if max_weekly > avg_weekly * 2 and max_weekly > 3:
        lines.append(f"⚠️ Spike in corrections during {max_week} ({max_weekly} items).")

    # Improvement suggestion
    if total > 20:
        lines.append("Action: Analyze common correction reasons to identify training opportunities.")

    lines.append("")
    return "\n".join(lines)


def analyze_throughput_by_member(output_dir: str, weeks: int = 6) -> str:
    """Analyze throughput by team member and return insights."""
    csv_path = os.path.join(output_dir, "throughput_by_member.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    # Filter to last N weeks
    all_weeks = sorted(df["week"].unique())
    recent_weeks = all_weeks[-weeks:] if len(all_weeks) >= weeks else all_weeks
    df = df[df["week"].isin(recent_weeks)]

    if df.empty:
        return ""

    member_totals = df.groupby("assignee")["issues_completed"].sum().sort_values(ascending=False)
    top_3 = member_totals.head(3)
    top_names = ", ".join(f"{name} ({count})" for name, count in top_3.items())
    total = member_totals.sum()
    num_members = len(member_totals)
    num_weeks = len(recent_weeks)

    # Calculate weekly average per member
    avg_per_member_per_week = member_totals.mean() / num_weeks if num_weeks > 0 else 0

    # Calculate concentration ratio (top 3 share)
    top_3_ratio = top_3.sum() / total * 100 if total > 0 else 0

    lines = [
        "THROUGHPUT BY MEMBER",
        "-" * 40,
        f"Top contributors (last {num_weeks} weeks): {top_names}.",
        f"Top 3 account for {top_3_ratio:.1f}% of team throughput ({total} issues total).",
        f"Team size: {num_members} members, averaging {avg_per_member_per_week:.1f} issues per person per week.",
    ]

    # Dependency on few members warning
    if top_3_ratio > 70 and num_members > 3:
        lines.append(f"⚠️ High concentration risk - top 3 members handle {top_3_ratio:.1f}% of output.")
        lines.append("Consider: Cross-train team members to reduce key person dependency.")

    # Low contributors (based on total over the period)
    avg_per_member_total = member_totals.mean()
    low_threshold = avg_per_member_total * 0.3
    low_contributors = member_totals[member_totals < low_threshold]
    if len(low_contributors) > 0 and len(low_contributors) < num_members:
        low_names = ", ".join(low_contributors.index.tolist()[:3])
        lines.append(f"⚠️ Low throughput members: {low_names} (<30% of average).")
        lines.append("Action: Check for blockers, onboarding needs, or non-ticket work.")

    # Single point of failure
    if num_members > 1:
        top_member_ratio = member_totals.iloc[0] / total * 100 if total > 0 else 0
        if top_member_ratio > 40:
            lines.append(f"⚠️ {member_totals.index[0]} handles {top_member_ratio:.1f}% of work - single point of failure risk.")

    lines.append("")
    return "\n".join(lines)


def analyze_wip_health(output_dir: str, months: int) -> str:
    """Analyze WIP health and return insights."""
    csv_path = os.path.join(output_dir, "wip_health.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    status_cols = ["To_Do", "In_Progress", "In_Review", "In_QA", "Correction_Required", "Awaiting_Feedback"]
    existing_cols = [c for c in status_cols if c in df.columns]
    totals = {c: df[c].sum() for c in existing_cols}
    grand_total = sum(totals.values())
    top_status = max(totals, key=totals.get) if totals else "N/A"
    top_count = totals.get(top_status, 0)

    # Calculate distribution ratios
    status_breakdown = ", ".join(
        f"{c.replace('_', ' ')}: {totals[c]}" for c in existing_cols if totals.get(c, 0) > 0
    )

    lines = [
        "WIP HEALTH",
        "-" * 40,
        f"Total {grand_total} items in WIP across all statuses.",
        f"Largest WIP category: {top_status.replace('_', ' ')} with {top_count} items.",
        f"Status breakdown: {status_breakdown}.",
    ]

    # Bottleneck detection
    if grand_total > 0:
        top_ratio = top_count / grand_total * 100
        if top_ratio > 50 and top_status != "In_Progress":
            lines.append(f"⚠️ Bottleneck in '{top_status.replace('_', ' ')}' - {top_ratio:.1f}% of WIP stuck here.")
            lines.append("Consider: Add reviewers or streamline the review process.")

    # Correction Required warning
    correction_count = totals.get("Correction_Required", 0)
    if correction_count > 3:
        lines.append(f"⚠️ {correction_count} items need corrections - prioritize fixing quality issues.")

    # Awaiting Feedback warning
    feedback_count = totals.get("Awaiting_Feedback", 0)
    if feedback_count > 5:
        lines.append(f"⚠️ {feedback_count} items awaiting feedback - follow up to unblock work.")

    # High WIP per person
    if grand_total > 0 and len(df) > 0:
        avg_wip = grand_total / len(df)
        if avg_wip > 5:
            lines.append(f"⚠️ Average {avg_wip:.1f} WIP items per person - exceeds recommended limit of 5.")
            lines.append("Action: Implement strict WIP limits to improve focus and flow.")

    lines.append("")
    return "\n".join(lines)


def analyze_bugs_cumulative(output_dir: str, months: int) -> str:
    """Analyze cumulative bug trend and return insights."""
    csv_path = os.path.join(output_dir, "bugs_cumulative.csv")
    if not os.path.exists(csv_path):
        return ""

    df = pd.read_csv(csv_path)
    if df.empty:
        return ""

    latest = df.iloc[-1]
    created = int(latest["cumulative_created"])
    resolved = int(latest["cumulative_resolved"])
    open_bugs = int(latest["open_bugs"])
    resolution_rate = resolved / created * 100 if created > 0 else 0

    # Calculate weekly resolution rate (recent)
    if len(df) >= 2:
        recent_resolved = int(df.iloc[-1]["cumulative_resolved"]) - int(df.iloc[-5]["cumulative_resolved"]) if len(df) >= 5 else resolved
        recent_created = int(df.iloc[-1]["cumulative_created"]) - int(df.iloc[-5]["cumulative_created"]) if len(df) >= 5 else created
        recent_ratio = recent_resolved / recent_created * 100 if recent_created > 0 else 0
    else:
        recent_ratio = resolution_rate

    # Trend for open bugs
    if len(df) >= 4:
        recent_open = df.tail(4)["open_bugs"].mean()
        earlier_open = df.tail(8).head(4)["open_bugs"].mean() if len(df) >= 8 else df["open_bugs"].mean()
        trend = "increasing" if recent_open > earlier_open * 1.1 else "decreasing" if recent_open < earlier_open * 0.9 else "stable"
    else:
        trend = "insufficient data"

    # Peak open bugs
    peak_open = df["open_bugs"].max()

    lines = [
        "BUGS CUMULATIVE",
        "-" * 40,
        f"Total {created} bugs created, {resolved} resolved ({resolution_rate:.1f}% resolution rate).",
        f"Currently {open_bugs} open bugs with {trend} trend. Peak was {peak_open} open bugs.",
    ]

    # Open bugs increasing warning
    if trend == "increasing":
        lines.append("⚠️ Open bug count is increasing - bugs being created faster than resolved.")
        lines.append("Consider: Allocate more capacity to bug fixes or investigate quality issues.")

    # Low resolution rate warning
    if resolution_rate < 80:
        lines.append(f"⚠️ Low resolution rate ({resolution_rate:.1f}%) - bug backlog is growing.")

    # Recent resolution performance
    if recent_ratio < 100:
        lines.append(f"⚠️ Recent resolution rate ({recent_ratio:.1f}%) below creation rate - backlog accumulating.")
    elif recent_ratio > 100:
        lines.append(f"Recent resolution rate ({recent_ratio:.1f}%) exceeding creation - backlog shrinking.")

    # High open bug count warning
    if open_bugs > 50:
        lines.append(f"⚠️ High open bug count ({open_bugs}) - consider a bug bash or dedicated fix sprint.")
        lines.append("Action: Prioritize critical bugs and close obsolete issues.")

    lines.append("")
    return "\n".join(lines)


def generate_analysis_report(output_dir: str, months: int = 6,
                             include_bug_cumulative: bool = False) -> None:
    """Generate analysis_results.txt with brief insights for all charts."""
    lines = [
        "JIRA METRICS ANALYSIS REPORT",
        "=" * 40,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Period: Last {months} months",
        "",
    ]

    # Call each analysis function and append results
    # Functions that use months parameter
    analysis_functions_months = [
        analyze_throughput,
        analyze_cycle_time,
        analyze_lead_time,
        analyze_status_distribution,
        analyze_issue_types,
        analyze_aging_wip,
        analyze_bugs_created,
        analyze_correction_required,
        analyze_wip_health,
    ]

    if include_bug_cumulative:
        analysis_functions_months.append(analyze_bugs_cumulative)

    for func in analysis_functions_months:
        result = func(output_dir, months)
        if result:
            lines.append(result)

    # Functions that use weeks parameter (6 weeks)
    analysis_functions_weeks = [
        analyze_workload,
        analyze_throughput_by_member,
    ]

    for func in analysis_functions_weeks:
        result = func(output_dir, weeks=6)
        if result:
            lines.append(result)

    with open(os.path.join(output_dir, "analysis_results.txt"), "w") as f:
        f.write("\n".join(lines))


def generate_all_charts(output_dir: str, verbose: bool = False, months: int = 6,
                        include_bug_cumulative: bool = False) -> None:
    """Generate all charts from CSV files in the output directory."""
    chart_functions = [
        ("Throughput", generate_throughput_chart, {"months": months}),
        ("Cycle Time", generate_cycle_time_chart, {"months": months}),
        ("Lead Time", generate_lead_time_chart, {"months": months}),
        ("Status Distribution", generate_status_distribution_chart, {"months": months}),
        ("Issue Types", generate_issue_types_chart, {"months": months}),
        ("Workload", generate_workload_chart, {"weeks": 6}),
        ("Aging WIP", generate_aging_wip_chart, {"months": months}),
        ("Bugs Created", generate_bugs_created_chart, {"months": months}),
        ("Correction Required", generate_correction_required_chart, {"months": months}),
        ("Throughput by Member", generate_throughput_by_member_chart, {"weeks": 6}),
        ("WIP Health", generate_wip_health_chart, {"months": months}),
    ]

    # Add cumulative bug chart if requested
    if include_bug_cumulative:
        chart_functions.append(("Bugs Cumulative", generate_bugs_cumulative_chart, {}))

    for name, func, kwargs in chart_functions:
        try:
            func(output_dir, **kwargs)
            if verbose:
                print(f"[INFO] Generated chart: {name}")
        except Exception as e:
            print(f"Warning: Failed to generate {name} chart: {e}")

    # Generate analysis report
    try:
        generate_analysis_report(output_dir, months, include_bug_cumulative)
        if verbose:
            print("[INFO] Generated analysis report")
    except Exception as e:
        print(f"Warning: Failed to generate analysis report: {e}")

    print(f"Charts saved to: {output_dir}/")
