"""
=============================================================================
Module: main.py
Project: Chess Player Performance Analytics Dashboard
Author: Data Analyst Intern
Description:
    Master pipeline runner script jo teeno stages ko sequential order me
    execute karta hai:
      Step 1: Data Collection (fetch_data.py) -> Chess.com API / GM Synthetic fallback
      Step 2: Exploratory Data Analysis (analyze.py) -> 8 Publication-grade PNG charts
      Step 3: Interactive Dashboard (dashboard.py) -> HTML Plotly Dashboard
    CLI argument se username ya force sample flag pass kiya ja sakta hai.
=============================================================================
"""

import os
import sys
import time
import argparse
from datetime import datetime

# Local imports
from fetch_data import collect_and_save_data
from analyze import run_analysis
from dashboard import generate_html_dashboard, load_dataset


# ---------------------------------------------------------------------------
# Path Defaults
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(BASE_DIR, "chess_games.csv")
OUTPUT_DIR_PATH = os.path.join(BASE_DIR, "output")
HTML_FILE_PATH = os.path.join(BASE_DIR, "chess_dashboard.html")


def print_banner():
    banner = """
================================================================================
       CHESS PLAYER PERFORMANCE ANALYTICS DASHBOARD - PIPELINE RUNNER
                   Data Analyst Internship Showcase Project
================================================================================
"""
    print(banner)


def run_pipeline(username: str = "hikaru",
                 force_sample: bool = False,
                 months: int = 4,
                 sample_games: int = 5000,
                 csv_path: str = CSV_FILE_PATH,
                 output_dir: str = OUTPUT_DIR_PATH,
                 html_path: str = HTML_FILE_PATH):
    """
    Complete end-to-end analytics workflow run karta hai.
    """
    start_time = time.time()
    print_banner()
    print(f"[*] Target Player Profile : @{username}")
    print(f"[*] Execution Mode        : {'Synthetic Sample Fallback' if force_sample else 'Live Chess.com API with Fallback'}")
    print(f"[*] Workspace Directory   : {BASE_DIR}")
    print(f"[*] Started At            : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # -----------------------------------------------------------------------
    # Step 1: Data Collection & Preprocessing
    # -----------------------------------------------------------------------
    print("\n>>> STEP 1: DATA COLLECTION & PREPROCESSING")
    print(f"    Fetching match records for '{username}'...")
    
    step1_start = time.time()
    df = collect_and_save_data(
        username=username,
        output_path=csv_path,
        force_sample=force_sample,
        months=months,
        sample_size=sample_games
    )
    print(f"[+] Step 1 Completed in {time.time() - step1_start:.2f}s | {len(df):,} games processed.")
    
    # -----------------------------------------------------------------------
    # Step 2: Exploratory Data Analysis & Publication Visualizations
    # -----------------------------------------------------------------------
    print("\n>>> STEP 2: EXPLORATORY DATA ANALYSIS & VISUALIZATION (Matplotlib/Seaborn)")
    print(f"    Generating 8 publication-grade charts in: {output_dir}...")
    
    step2_start = time.time()
    run_analysis(csv_path=csv_path, output_dir=output_dir)
    print(f"[+] Step 2 Completed in {time.time() - step2_start:.2f}s | 8 PNG figures generated.")
    
    # -----------------------------------------------------------------------
    # Step 3: Interactive Plotly HTML Dashboard Generation
    # -----------------------------------------------------------------------
    print("\n>>> STEP 3: INTERACTIVE HTML DASHBOARD GENERATION (Plotly)")
    print(f"    Compiling executive dashboard: {html_path}...")
    
    step3_start = time.time()
    loaded_df = load_dataset(csv_path)
    generate_html_dashboard(df=loaded_df, output_html=html_path, username=username)
    print(f"[+] Step 3 Completed in {time.time() - step3_start:.2f}s | Interactive Dashboard ready.")
    
    # -----------------------------------------------------------------------
    # Final Pipeline Summary
    # -----------------------------------------------------------------------
    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("                    ALL PIPELINE STAGES COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"[✔] Total Execution Time : {total_time:.2f} seconds")
    print(f"[✔] Match Dataset Saved   : {csv_path}")
    print(f"[✔] Visualizations Folder : {output_dir}")
    print(f"    -> 01_opening_win_rates.png")
    print(f"    -> 02_rating_trend.png")
    print(f"    -> 03_time_of_day_performance.png")
    print(f"    -> 04_game_duration_distribution.png")
    print(f"    -> 05_win_rate_by_color.png")
    print(f"    -> 06_monthly_games_played.png")
    print(f"    -> 07_result_distribution.png")
    print(f"    -> 08_rating_vs_game_duration.png")
    print(f"[✔] Interactive Dashboard : {html_path}")
    print(f"\n[Tip] Open 'chess_dashboard.html' in any browser to inspect interactive graphs!")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run Chess Player Performance Analytics end-to-end pipeline."
    )
    parser.add_argument("username", nargs="?", default="hikaru",
                        help="Chess.com username to analyze (default: 'hikaru')")
    parser.add_argument("--sample", "-s", action="store_true",
                        help="Force generate synthetic Grandmaster dataset (~5000 games)")
    parser.add_argument("--months", "-m", type=int, default=4,
                        help="Number of monthly archives to query from Chess.com API (default: 4)")
    parser.add_argument("--games", "-g", type=int, default=5000,
                        help="Number of games to generate if running sample mode (default: 5000)")
    parser.add_argument("--output-dir", "-o", default=OUTPUT_DIR_PATH,
                        help="Directory for output visualization PNG images")
    parser.add_argument("--csv", default=CSV_FILE_PATH,
                        help="Path for output chess_games.csv file")
    parser.add_argument("--html", default=HTML_FILE_PATH,
                        help="Path for interactive chess_dashboard.html")
    
    args = parser.parse_args()
    
    run_pipeline(
        username=args.username,
        force_sample=args.sample,
        months=args.months,
        sample_games=args.games,
        csv_path=args.csv,
        output_dir=args.output_dir,
        html_path=args.html
    )


if __name__ == "__main__":
    main()
