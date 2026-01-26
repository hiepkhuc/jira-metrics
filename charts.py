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


def generate_throughput_chart(output_dir: str) -> None:
    """Generate weekly throughput chart with issues and story points."""
    csv_path = os.path.join(output_dir, "weekly_throughput.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)
    df = df.sort_values("date")

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart for issues completed
    bars = ax1.bar(df["date"], df["issues_completed"], width=5, alpha=0.7,
                   color="#4CAF50", label="Issues Completed")
    ax1.set_xlabel("Week")
    ax1.set_ylabel("Issues Completed", color="#4CAF50")
    ax1.tick_params(axis="y", labelcolor="#4CAF50")

    # Line chart for story points on secondary axis
    ax2 = ax1.twinx()
    line = ax2.plot(df["date"], df["story_points_completed"], color="#2196F3",
                    linewidth=2, marker="o", markersize=4, label="Story Points")
    ax2.set_ylabel("Story Points", color="#2196F3")
    ax2.tick_params(axis="y", labelcolor="#2196F3")

    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-W%W"))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=max(1, len(df) // 10)))
    plt.xticks(rotation=45, ha="right")

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.title("Weekly Throughput")
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

    plt.title("Cycle Time Trend")
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

    plt.title("Lead Time Trend (Created to Done)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_lead_time.png"), dpi=150)
    plt.close()


def generate_status_distribution_chart(output_dir: str) -> None:
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

    plt.title("Status Distribution")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_status_distribution.png"), dpi=150)
    plt.close()


def generate_issue_types_chart(output_dir: str) -> None:
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

    plt.title("Issue Types Distribution")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_issue_types.png"), dpi=150)
    plt.close()


def generate_workload_chart(output_dir: str) -> None:
    """Generate stacked horizontal bar chart for assignee workload."""
    csv_path = os.path.join(output_dir, "assignee_workload.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Calculate "other" issues (total - in_progress)
    df["other"] = df["total_issues"] - df["in_progress"]

    # Sort by in_progress descending, take top 15
    df = df.sort_values("in_progress", ascending=False).head(15)
    df = df.sort_values("in_progress", ascending=True)  # Reverse for horizontal bar

    fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))

    # Stacked horizontal bars
    ax.barh(df["assignee"], df["in_progress"], color="#F44336", label="In Progress")
    ax.barh(df["assignee"], df["other"], left=df["in_progress"], color="#BDBDBD",
            label="Other")

    ax.set_xlabel("Number of Issues")
    ax.set_ylabel("Assignee")
    ax.legend(loc="lower right")

    plt.title("Assignee Workload (Top 15)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "chart_workload.png"), dpi=150)
    plt.close()


def generate_aging_wip_chart(output_dir: str) -> None:
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

    plt.title("Aging Work In Progress (Top 20)")
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

    plt.title("Bugs Created Weekly by Priority")
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

    plt.title("Weekly Tickets Moved to 'Correction Required'")
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


def generate_all_charts(output_dir: str, verbose: bool = False, months: int = 6,
                        include_bug_cumulative: bool = False) -> None:
    """Generate all charts from CSV files in the output directory."""
    chart_functions = [
        ("Throughput", generate_throughput_chart, {}),
        ("Cycle Time", generate_cycle_time_chart, {"months": months}),
        ("Lead Time", generate_lead_time_chart, {"months": months}),
        ("Status Distribution", generate_status_distribution_chart, {}),
        ("Issue Types", generate_issue_types_chart, {}),
        ("Workload", generate_workload_chart, {}),
        ("Aging WIP", generate_aging_wip_chart, {}),
        ("Bugs Created", generate_bugs_created_chart, {"months": months}),
        ("Correction Required", generate_correction_required_chart, {"months": months}),
        ("Throughput by Member", generate_throughput_by_member_chart, {"weeks": 6}),
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

    print(f"Charts saved to: {output_dir}/")
