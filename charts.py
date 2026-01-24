"""
Chart generation for JIRA metrics.

Generates PNG charts from the CSV files produced by jira_metrics.py.
"""

import os
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


def generate_cycle_time_chart(output_dir: str) -> None:
    """Generate cycle time trend chart with min/max range."""
    csv_path = os.path.join(output_dir, "cycle_time_weekly.csv")
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    df["date"] = df["week"].apply(parse_week)
    df = df.sort_values("date")

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


def generate_all_charts(output_dir: str, verbose: bool = False) -> None:
    """Generate all charts from CSV files in the output directory."""
    chart_functions = [
        ("Throughput", generate_throughput_chart),
        ("Cycle Time", generate_cycle_time_chart),
        ("Status Distribution", generate_status_distribution_chart),
        ("Issue Types", generate_issue_types_chart),
        ("Workload", generate_workload_chart),
        ("Aging WIP", generate_aging_wip_chart),
    ]

    for name, func in chart_functions:
        try:
            func(output_dir)
            if verbose:
                print(f"[INFO] Generated chart: {name}")
        except Exception as e:
            print(f"Warning: Failed to generate {name} chart: {e}")

    print(f"Charts saved to: {output_dir}/")
