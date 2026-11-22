"""
=============================================================================
Module: analyze.py
Project: Chess Player Performance Analytics Dashboard
Author: Data Analyst Intern
Description:
    Yeh module chess_games.csv dataset ko load karke exploratory data analysis
    (EDA) karta hai aur 8 publication-quality visualizations create karta hai:
      1. Win Rate by Opening (Top 15 openings horizontal stacked bar chart)
      2. Rating Trend Over Time (Progression with peak/trough annotations)
      3. Performance by Time of Day (Morning/Afternoon/Evening/Night)
      4. Game Duration Distribution (Move counts histogram with KDE)
      5. Win Rate by Color (White vs Black dual donut/pie charts)
      6. Monthly Games Played (Activity volume with win rate trend)
      7. Result Distribution (Career Win/Loss/Draw donut chart)
      8. Rating vs Game Duration (Opponent rating vs moves scatter plot)
    Saari charts dark professional theme me 'output/' folder me PNG format
    me save hoti hain, aur terminal par detailed summary statistics print hoti hain.
=============================================================================
"""

import os
import sys
import argparse
from typing import Tuple, Dict, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.join(CURRENT_DIR, "chess_games.csv")
DEFAULT_OUTPUT_DIR = os.path.join(CURRENT_DIR, "output")

# ---------------------------------------------------------------------------
# Dark Professional Chess Theme Configuration
# ---------------------------------------------------------------------------
CHESS_THEME = {
    "bg_dark": "#12151c",       # Overall figure background
    "bg_card": "#1a1f2c",       # Axes / plot background
    "text_primary": "#f1f5f9",  # Crisp white-slate text
    "text_muted": "#94a3b8",    # Subdued gray text
    "grid_color": "#283042",    # Subtle grid lines
    "win_color": "#2ecc71",     # Vibrant Emerald green
    "loss_color": "#ef4444",    # Crimson red
    "draw_color": "#94a3b8",    # Neutral cool gray
    "gold_accent": "#f59e0b",   # Golden chess highlight
    "cyan_accent": "#06b6d4",   # Cyber cyan for trend lines
    "purple_accent": "#a855f7", # Violet accent
}

def apply_chess_dark_theme():
    """
    Matplotlib and Seaborn ke liye dark professional chess theme apply karta hai.
    """
    plt.rcParams.update({
        "figure.facecolor": CHESS_THEME["bg_dark"],
        "axes.facecolor": CHESS_THEME["bg_card"],
        "savefig.facecolor": CHESS_THEME["bg_dark"],
        "text.color": CHESS_THEME["text_primary"],
        "axes.labelcolor": CHESS_THEME["text_primary"],
        "xtick.color": CHESS_THEME["text_muted"],
        "ytick.color": CHESS_THEME["text_muted"],
        "axes.edgecolor": CHESS_THEME["grid_color"],
        "axes.linewidth": 1.2,
        "grid.color": CHESS_THEME["grid_color"],
        "grid.linestyle": "--",
        "grid.alpha": 0.5,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
        "figure.autolayout": False,
    })


# ---------------------------------------------------------------------------
# Data Loading & Preprocessing
# ---------------------------------------------------------------------------
def load_and_preprocess_data(csv_path: str = DEFAULT_CSV_PATH) -> pd.DataFrame:
    """
    CSV file se chess games load karke datetime aur derived metrics prepare karta hai.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset nahi mila: {csv_path}. Kripya pehle fetch_data.py chalayein!")
        
    df = pd.read_csv(csv_path)
    
    # Date & time conversion
    df["date"] = pd.to_datetime(df["date"])
    df["month_year"] = df["date"].dt.strftime("%Y-%m")
    
    # Result standardization
    df["result"] = df["result"].str.lower().str.strip()
    valid_results = {"win", "loss", "draw"}
    df["result"] = df["result"].apply(lambda r: r if r in valid_results else "loss")
    
    # Ensure numeric columns are clean
    df["player_rating"] = pd.to_numeric(df["player_rating"], errors="coerce").fillna(3150).astype(int)
    df["opponent_rating"] = pd.to_numeric(df["opponent_rating"], errors="coerce").fillna(3150).astype(int)
    df["num_moves"] = pd.to_numeric(df["num_moves"], errors="coerce").fillna(38).astype(int)
    
    # Sorting chronologically
    df = df.sort_values(by="date").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 8 Publication-Quality Visualizations
# ---------------------------------------------------------------------------

def plot_opening_win_rates(df: pd.DataFrame, output_dir: str):
    """
    Chart 1: Win Rate by Opening (Top 15 Openings)
    Horizontal stacked bar chart with Green (Win), Gray (Draw), Red (Loss)
    """
    # Top 15 openings by frequency
    top_openings = df["opening"].value_counts().head(15).index.tolist()
    filtered = df[df["opening"].isin(top_openings)]
    
    # Har opening ke liye win/draw/loss proportions calculate karte hain
    grouped = pd.crosstab(filtered["opening"], filtered["result"], normalize="index") * 100
    for col in ["win", "draw", "loss"]:
        if col not in grouped.columns:
            grouped[col] = 0.0
    
    grouped = grouped[["win", "draw", "loss"]]
    # Win rate ke basis par sort karte hain ascending order taaki highest top par dikhe
    grouped = grouped.loc[top_openings].sort_values(by="win", ascending=True)
    
    # Total games per opening for annotations
    counts = filtered["opening"].value_counts().to_dict()
    
    fig, ax = plt.subplots(figsize=(13, 8.5), dpi=300)
    y_pos = np.arange(len(grouped))
    
    win_pct = grouped["win"].values
    draw_pct = grouped["draw"].values
    loss_pct = grouped["loss"].values
    
    # Stacked bars
    b1 = ax.barh(y_pos, win_pct, color=CHESS_THEME["win_color"], edgecolor="#12151c", height=0.65, label="Win %")
    b2 = ax.barh(y_pos, draw_pct, left=win_pct, color=CHESS_THEME["draw_color"], edgecolor="#12151c", height=0.65, label="Draw %")
    b3 = ax.barh(y_pos, loss_pct, left=win_pct + draw_pct, color=CHESS_THEME["loss_color"], edgecolor="#12151c", height=0.65, label="Loss %")
    
    # Percentage labels inside bars
    for idx in range(len(grouped)):
        w = win_pct[idx]
        d = draw_pct[idx]
        l = loss_pct[idx]
        if w >= 12:
            ax.text(w / 2, idx, f"{w:.1f}%", va="center", ha="center", color="#0f172a", fontweight="bold", fontsize=9.5)
        if d >= 9:
            ax.text(w + d / 2, idx, f"{d:.1f}%", va="center", ha="center", color="#0f172a", fontweight="bold", fontsize=8.5)
        if l >= 10:
            ax.text(w + d + l / 2, idx, f"{l:.1f}%", va="center", ha="center", color="#ffffff", fontweight="bold", fontsize=8.5)
            
    # Y-axis labels with total game counts
    y_labels = [f"{op[:34]}.. ({counts.get(op, 0)} games)" if len(op) > 34 else f"{op} ({counts.get(op, 0)} games)" for op in grouped.index]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=10, fontweight="medium")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentage of Games (%)", fontsize=11, fontweight="bold", labelpad=10)
    
    ax.set_title("Top 15 Most Played Openings - Win / Draw / Loss Distribution",
                 fontsize=14, fontweight="bold", pad=20, color=CHESS_THEME["text_primary"])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=3, frameon=True,
              facecolor=CHESS_THEME["bg_card"], edgecolor=CHESS_THEME["grid_color"])
    ax.grid(axis="x", alpha=0.3)
    
    plt.tight_layout()
    out_file = os.path.join(output_dir, "01_opening_win_rates.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


def plot_rating_trend(df: pd.DataFrame, output_dir: str):
    """
    Chart 2: Rating Trend Over Time
    Line chart showing rating progression with rolling average, peak, and lowest ratings.
    """
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    
    # 50-game rolling moving average for smoothness
    df["rolling_rating"] = df["player_rating"].rolling(window=30, min_periods=5).mean()
    
    # Peak & Trough identification
    peak_idx = df["player_rating"].idxmax()
    peak_rating = df.loc[peak_idx, "player_rating"]
    peak_date = df.loc[peak_idx, "date"].strftime("%b %d, %Y")
    
    min_idx = df["player_rating"].idxmin()
    min_rating = df.loc[min_idx, "player_rating"]
    min_date = df.loc[min_idx, "date"].strftime("%b %d, %Y")
    
    curr_rating = df.iloc[-1]["player_rating"]
    
    # Plotting raw scatter and smooth trendline
    ax.scatter(df["date"], df["player_rating"], color=CHESS_THEME["cyan_accent"], alpha=0.15, s=12, label="Individual Game Rating")
    ax.plot(df["date"], df["rolling_rating"], color=CHESS_THEME["gold_accent"], linewidth=2.5, label="30-Game Moving Average")
    
    # Peak Rating Annotation
    ax.scatter(df.loc[peak_idx, "date"], peak_rating, color="#22c55e", s=130, zorder=5, edgecolor="#ffffff", linewidth=1.5)
    ax.annotate(f"Peak: {peak_rating}\n({peak_date})",
                xy=(df.loc[peak_idx, "date"], peak_rating),
                xytext=(0, 26), textcoords="offset points", ha="center",
                arrowprops=dict(arrowstyle="->", color="#22c55e", lw=1.5),
                bbox=dict(boxstyle="round,pad=0.4", fc=CHESS_THEME["bg_card"], ec="#22c55e", lw=1.2),
                fontsize=9.5, fontweight="bold", color="#22c55e")
                
    # Lowest Rating Annotation
    ax.scatter(df.loc[min_idx, "date"], min_rating, color="#ef4444", s=130, zorder=5, edgecolor="#ffffff", linewidth=1.5)
    ax.annotate(f"Trough: {min_rating}\n({min_date})",
                xy=(df.loc[min_idx, "date"], min_rating),
                xytext=(0, -38), textcoords="offset points", ha="center",
                arrowprops=dict(arrowstyle="->", color="#ef4444", lw=1.5),
                bbox=dict(boxstyle="round,pad=0.4", fc=CHESS_THEME["bg_card"], ec="#ef4444", lw=1.2),
                fontsize=9.5, fontweight="bold", color="#ef4444")
                
    ax.set_title("Performance Rating Progression Over Time", fontsize=14, fontweight="bold", pad=18)
    ax.set_xlabel("Date Timeline", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_ylabel("Chess Rating (Elo)", fontsize=11, fontweight="bold", labelpad=10)
    
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))
    ax.grid(True, alpha=0.35)
    ax.legend(loc="lower right", frameon=True, facecolor=CHESS_THEME["bg_card"], edgecolor=CHESS_THEME["grid_color"])
    
    plt.tight_layout()
    out_file = os.path.join(output_dir, "02_rating_trend.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


def plot_time_of_day_performance(df: pd.DataFrame, output_dir: str):
    """
    Chart 3: Performance by Time of Day
    Grouped bar chart for Morning, Afternoon, Evening, Night (Win/Draw/Loss rates).
    """
    time_order = ["Morning", "Afternoon", "Evening", "Night"]
    
    # Filter only available valid time categories
    grouped = pd.crosstab(df["time_of_day"], df["result"], normalize="index") * 100
    for col in ["win", "draw", "loss"]:
        if col not in grouped.columns:
            grouped[col] = 0.0
            
    # Reindex according to natural diurnal order
    grouped = grouped.reindex([t for t in time_order if t in grouped.index])
    game_counts = df["time_of_day"].value_counts().to_dict()
    
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    x = np.arange(len(grouped))
    bar_width = 0.25
    
    # 3 grouped bars
    r1 = ax.bar(x - bar_width, grouped["win"], width=bar_width, color=CHESS_THEME["win_color"],
                edgecolor=CHESS_THEME["bg_dark"], label="Win %")
    r2 = ax.bar(x, grouped["draw"], width=bar_width, color=CHESS_THEME["draw_color"],
                edgecolor=CHESS_THEME["bg_dark"], label="Draw %")
    r3 = ax.bar(x + bar_width, grouped["loss"], width=bar_width, color=CHESS_THEME["loss_color"],
                edgecolor=CHESS_THEME["bg_dark"], label="Loss %")
                
    # Labels above bars
    for bars in [r1, r2, r3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8.5, fontweight="bold")
                        
    x_labels = [f"{t}\n({game_counts.get(t, 0):,} games)" for t in grouped.index]
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=10.5, fontweight="medium")
    ax.set_ylim(0, max(grouped["win"].max(), 85) + 12)
    ax.set_ylabel("Win / Draw / Loss Rate (%)", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_title("Performance & Win Rate by Time of Day", fontsize=14, fontweight="bold", pad=18)
    
    ax.legend(loc="upper right", frameon=True, facecolor=CHESS_THEME["bg_card"], edgecolor=CHESS_THEME["grid_color"])
    ax.grid(axis="y", alpha=0.35)
    
    plt.tight_layout()
    out_file = os.path.join(output_dir, "03_time_of_day_performance.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


def plot_game_duration_distribution(df: pd.DataFrame, output_dir: str):
    """
    Chart 4: Game Duration Distribution
    Histogram of number of moves with KDE curve and mean/median indicators.
    """
    moves = df["num_moves"].dropna()
    mean_moves = moves.mean()
    median_moves = moves.median()
    
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=300)
    
    # Histogram + KDE
    sns.histplot(moves, kde=True, ax=ax, color=CHESS_THEME["cyan_accent"],
                 bins=35, edgecolor=CHESS_THEME["bg_dark"], alpha=0.7, stat="density")
                 
    # Vertical lines for statistics
    ax.axvline(mean_moves, color=CHESS_THEME["gold_accent"], linestyle="--", linewidth=2.2,
               label=f"Mean Moves: {mean_moves:.1f}")
    ax.axvline(median_moves, color="#ec4899", linestyle=":", linewidth=2.2,
               label=f"Median Moves: {median_moves:.0f}")
               
    # Annotations
    ax.set_title("Game Duration Distribution (Move Count per Game)", fontsize=14, fontweight="bold", pad=18)
    ax.set_xlabel("Number of Full Moves in Game", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_ylabel("Density of Games", fontsize=11, fontweight="bold", labelpad=10)
    
    ax.grid(axis="y", alpha=0.35)
    ax.legend(loc="upper right", frameon=True, facecolor=CHESS_THEME["bg_card"], edgecolor=CHESS_THEME["grid_color"], fontsize=10)
    
    plt.tight_layout()
    out_file = os.path.join(output_dir, "04_game_duration_distribution.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


def plot_win_rate_by_color(df: pd.DataFrame, output_dir: str):
    """
    Chart 5: Win Rate by Color
    Dual Donut / Pie Charts comparing White vs Black performance.
    """
    white_games = df[df["player_color"] == "White"]
    black_games = df[df["player_color"] == "Black"]
    
    labels = ["Win", "Draw", "Loss"]
    palette = [CHESS_THEME["win_color"], CHESS_THEME["draw_color"], CHESS_THEME["loss_color"]]
    
    def get_counts(sub_df):
        vc = sub_df["result"].value_counts()
        return [vc.get("win", 0), vc.get("draw", 0), vc.get("loss", 0)]
        
    white_vals = get_counts(white_games)
    black_vals = get_counts(black_games)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), dpi=300)
    
    # White pie
    wedges1, texts1, autotexts1 = ax1.pie(
        white_vals, labels=labels, autopct="%1.1f%%", startangle=140,
        colors=palette, explode=(0.04, 0.02, 0.02),
        wedgeprops=dict(width=0.45, edgecolor=CHESS_THEME["bg_dark"], linewidth=2)
    )
    for at in autotexts1:
        at.set_color("#0f172a")
        at.set_fontweight("bold")
    ax1.set_title(f"As White ({len(white_games):,} Games)\nWin Rate: {white_vals[0]/len(white_games)*100:.1f}%",
                  fontsize=12, fontweight="bold", color=CHESS_THEME["text_primary"])
                  
    # Black pie
    wedges2, texts2, autotexts2 = ax2.pie(
        black_vals, labels=labels, autopct="%1.1f%%", startangle=140,
        colors=palette, explode=(0.04, 0.02, 0.02),
        wedgeprops=dict(width=0.45, edgecolor=CHESS_THEME["bg_dark"], linewidth=2)
    )
    for at in autotexts2:
        at.set_color("#0f172a")
        at.set_fontweight("bold")
    ax2.set_title(f"As Black ({len(black_games):,} Games)\nWin Rate: {black_vals[0]/len(black_games)*100:.1f}%",
                  fontsize=12, fontweight="bold", color=CHESS_THEME["text_primary"])
                  
    fig.suptitle("Performance Comparison: Playing with White vs Black Pieces",
                 fontsize=15, fontweight="bold", y=0.98, color=CHESS_THEME["text_primary"])
                 
    plt.tight_layout()
    out_file = os.path.join(output_dir, "05_win_rate_by_color.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


def plot_monthly_games_played(df: pd.DataFrame, output_dir: str):
    """
    Chart 6: Monthly Games Played
    Bar chart showing monthly game activity with win-rate line overlay.
    """
    monthly = df.groupby("month_year").agg(
        total_games=("result", "count"),
        wins=("result", lambda r: (r == "win").sum())
    ).reset_index()
    monthly["win_rate"] = (monthly["wins"] / monthly["total_games"]) * 100
    
    fig, ax1 = plt.subplots(figsize=(13, 6.5), dpi=300)
    
    x = np.arange(len(monthly))
    bars = ax1.bar(x, monthly["total_games"], color=CHESS_THEME["purple_accent"],
                   alpha=0.85, edgecolor=CHESS_THEME["bg_dark"], width=0.55, label="Games Played")
                   
    # Secondary axis for win rate line
    ax2 = ax1.twinx()
    line = ax2.plot(x, monthly["win_rate"], color=CHESS_THEME["gold_accent"],
                    marker="o", linewidth=2.5, markersize=7, label="Win Rate %")
                    
    # Value annotations on bars
    for bar in bars:
        h = bar.get_height()
        ax1.annotate(f"{int(h)}",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=CHESS_THEME["text_primary"])
                     
    ax1.set_xticks(x)
    ax1.set_xticklabels(monthly["month_year"], rotation=45, ha="right", fontsize=9.5)
    ax1.set_ylabel("Number of Games Played", fontsize=11, fontweight="bold", color=CHESS_THEME["text_primary"], labelpad=10)
    ax2.set_ylabel("Monthly Win Rate (%)", fontsize=11, fontweight="bold", color=CHESS_THEME["gold_accent"], labelpad=10)
    ax2.set_ylim(40, 100)
    
    ax1.set_title("Monthly Activity Volume & Performance Trajectory", fontsize=14, fontweight="bold", pad=18)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=True,
               facecolor=CHESS_THEME["bg_card"], edgecolor=CHESS_THEME["grid_color"])
               
    ax1.grid(axis="y", alpha=0.3)
    ax2.grid(False)
    
    plt.tight_layout()
    out_file = os.path.join(output_dir, "06_monthly_games_played.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


def plot_result_distribution(df: pd.DataFrame, output_dir: str):
    """
    Chart 7: Result Distribution
    Donut chart of overall career Win / Loss / Draw percentages with center KPI text.
    """
    total = len(df)
    res_counts = df["result"].value_counts()
    wins = res_counts.get("win", 0)
    draws = res_counts.get("draw", 0)
    losses = res_counts.get("loss", 0)
    
    vals = [wins, draws, losses]
    labels = ["Wins", "Draws", "Losses"]
    colors = [CHESS_THEME["win_color"], CHESS_THEME["draw_color"], CHESS_THEME["loss_color"]]
    
    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=300)
    
    wedges, texts, autotexts = ax.pie(
        vals,
        labels=[f"{l}\n({v:,})" for l, v in zip(labels, vals)],
        autopct="%1.1f%%",
        pctdistance=0.75,
        startangle=130,
        colors=colors,
        explode=(0.04, 0.02, 0.02),
        wedgeprops=dict(width=0.42, edgecolor=CHESS_THEME["bg_dark"], linewidth=2.5),
        textprops=dict(color=CHESS_THEME["text_primary"], fontsize=10.5, fontweight="medium")
    )
    
    for autotext in autotexts:
        autotext.set_color("#0f172a")
        autotext.set_fontweight("bold")
        autotext.set_fontsize(11)
        
    # Center text KPI
    ax.text(0, 0.08, f"{total:,}", ha="center", va="center", fontsize=22, fontweight="bold", color=CHESS_THEME["text_primary"])
    ax.text(0, -0.12, "Total Games\nAnalyzed", ha="center", va="center", fontsize=10, color=CHESS_THEME["text_muted"])
    
    ax.set_title("Overall Game Result Distribution", fontsize=15, fontweight="bold", pad=20)
    
    plt.tight_layout()
    out_file = os.path.join(output_dir, "07_result_distribution.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


def plot_rating_vs_game_duration(df: pd.DataFrame, output_dir: str):
    """
    Chart 8: Rating vs Game Duration
    Scatter plot of Opponent Rating vs Number of Moves, categorized by Game Result.
    """
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    
    color_map = {
        "win": CHESS_THEME["win_color"],
        "draw": CHESS_THEME["draw_color"],
        "loss": CHESS_THEME["loss_color"]
    }
    
    # Subsample if dataset is very large to avoid visual clutter
    plot_df = df.sample(min(len(df), 1500), random_state=42) if len(df) > 1500 else df
    
    for res in ["win", "draw", "loss"]:
        sub = plot_df[plot_df["result"] == res]
        ax.scatter(sub["opponent_rating"], sub["num_moves"],
                   c=color_map[res], label=res.capitalize(),
                   alpha=0.55, s=28, edgecolors="none")
                   
    # Linear Trendline
    z = np.polyfit(plot_df["opponent_rating"], plot_df["num_moves"], 1)
    p = np.poly1d(z)
    x_vals = np.linspace(plot_df["opponent_rating"].min(), plot_df["opponent_rating"].max(), 100)
    ax.plot(x_vals, p(x_vals), color=CHESS_THEME["gold_accent"], linestyle="--", linewidth=2.2,
            label=f"Trendline (slope: {z[0]:.2f})")
            
    ax.set_title("Game Duration (Moves) vs Opponent Rating by Outcome", fontsize=14, fontweight="bold", pad=18)
    ax.set_xlabel("Opponent Rating (Elo)", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_ylabel("Total Number of Moves", fontsize=11, fontweight="bold", labelpad=10)
    
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", frameon=True, facecolor=CHESS_THEME["bg_card"], edgecolor=CHESS_THEME["grid_color"])
    
    plt.tight_layout()
    out_file = os.path.join(output_dir, "08_rating_vs_game_duration.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[Saved] {out_file}")


# ---------------------------------------------------------------------------
# Summary Statistics Console Printer
# ---------------------------------------------------------------------------
def print_summary_statistics(df: pd.DataFrame):
    """
    Console par clean executive summary statistics print karta hai.
    """
    total_games = len(df)
    res_counts = df["result"].value_counts()
    wins = res_counts.get("win", 0)
    draws = res_counts.get("draw", 0)
    losses = res_counts.get("loss", 0)
    
    win_pct = (wins / total_games) * 100
    draw_pct = (draws / total_games) * 100
    loss_pct = (losses / total_games) * 100
    
    # Rating stats
    peak_rating = df["player_rating"].max()
    lowest_rating = df["player_rating"].min()
    current_rating = df.iloc[-1]["player_rating"]
    avg_rating = df["player_rating"].mean()
    
    # White vs Black stats
    white_games = df[df["player_color"] == "White"]
    black_games = df[df["player_color"] == "Black"]
    white_win_rate = (white_games["result"] == "win").mean() * 100 if len(white_games) > 0 else 0
    black_win_rate = (black_games["result"] == "win").mean() * 100 if len(black_games) > 0 else 0
    
    # Best & Most played opening
    most_played_op = df["opening"].mode()[0]
    op_counts = df["opening"].value_counts()
    significant_ops = op_counts[op_counts >= 20].index
    
    if len(significant_ops) > 0:
        sig_df = df[df["opening"].isin(significant_ops)]
        best_op_sr = sig_df.groupby("opening")["result"].apply(lambda r: (r == "win").mean() * 100)
        best_op_name = best_op_sr.idxmax()
        best_op_winrate = best_op_sr.max()
    else:
        best_op_name = most_played_op
        best_op_winrate = win_pct
        
    # Time of Day best performance
    tod_sr = df.groupby("time_of_day")["result"].apply(lambda r: (r == "win").mean() * 100)
    best_tod = tod_sr.idxmax()
    best_tod_winrate = tod_sr.max()
    
    # Average moves
    avg_moves = df["num_moves"].mean()
    median_moves = df["num_moves"].median()
    
    divider = "=" * 70
    sub_divider = "-" * 70
    
    print("\n" + divider)
    print("       CHESS PLAYER PERFORMANCE ANALYTICS - EXECUTIVE SUMMARY       ")
    print(divider)
    print(f"[*] Dataset Overview:")
    print(f"    - Total Games Analyzed : {total_games:,}")
    print(f"    - Date Timeline        : {df['date'].min().strftime('%d %b %Y')} to {df['date'].max().strftime('%d %b %Y')}")
    print(f"    - Overall Win Rate     : {win_pct:.2f}% (Wins: {wins:,})")
    print(f"    - Overall Draw Rate    : {draw_pct:.2f}% (Draws: {draws:,})")
    print(f"    - Overall Loss Rate    : {loss_pct:.2f}% (Losses: {losses:,})")
    print(sub_divider)
    print(f"[*] Rating & Elo Performance:")
    print(f"    - Peak Rating Achieved : {peak_rating}")
    print(f"    - Lowest Rating        : {lowest_rating}")
    print(f"    - Latest Rating        : {current_rating}")
    print(f"    - Average Rating       : {avg_rating:.1f}")
    print(sub_divider)
    print(f"[*] Color Performance Comparison:")
    print(f"    - As White Pieces      : {len(white_games):,} games | Win Rate: {white_win_rate:.2f}%")
    print(f"    - As Black Pieces      : {len(black_games):,} games | Win Rate: {black_win_rate:.2f}%")
    print(f"    - White Advantage      : +{white_win_rate - black_win_rate:.2f}% higher win rate")
    print(sub_divider)
    print(f"[*] Tactical Insights & Openings:")
    print(f"    - Most Played Opening  : {most_played_op} ({op_counts[most_played_op]} games)")
    print(f"    - Highest Win Rate Op  : {best_op_name} ({best_op_winrate:.1f}% win rate)")
    print(f"    - Golden Time of Day   : {best_tod} ({best_tod_winrate:.1f}% win rate)")
    print(f"    - Average Game Moves   : {avg_moves:.1f} moves (Median: {median_moves:.0f})")
    print(divider + "\n")


# ---------------------------------------------------------------------------
# Main Runner for Analysis Module
# ---------------------------------------------------------------------------
def run_analysis(csv_path: str = DEFAULT_CSV_PATH, output_dir: str = DEFAULT_OUTPUT_DIR):
    """
    Analysis pipeline run karta hai aur sabhi 8 plots generate karta hai.
    """
    print(f"[*] Loading chess dataset from: {csv_path}")
    df = load_and_preprocess_data(csv_path)
    
    os.makedirs(output_dir, exist_ok=True)
    apply_chess_dark_theme()
    
    print(f"[*] Generating 8 publication-ready visualizations into '{output_dir}'...")
    
    plot_opening_win_rates(df, output_dir)
    plot_rating_trend(df, output_dir)
    plot_time_of_day_performance(df, output_dir)
    plot_game_duration_distribution(df, output_dir)
    plot_win_rate_by_color(df, output_dir)
    plot_monthly_games_played(df, output_dir)
    plot_result_distribution(df, output_dir)
    plot_rating_vs_game_duration(df, output_dir)
    
    print("\n[OK] All 8 publication-quality charts saved successfully!")
    print_summary_statistics(df)


def main():
    parser = argparse.ArgumentParser(description="Analyze chess player performance and generate visualizations.")
    parser.add_argument("--input", "-i", default=DEFAULT_CSV_PATH, help="Path to input chess_games.csv")
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR, help="Directory to save PNG plots")
    
    args = parser.parse_args()
    run_analysis(args.input, args.output_dir)


if __name__ == "__main__":
    main()
