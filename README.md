# ♟ Chess Player Performance Analytics Dashboard

> **Data Analyst Internship Portfolio Project**  
> A production-ready, end-to-end data analytics and interactive visualization pipeline evaluating Chess.com Grandmaster performance.

---

## 📌 Executive Summary

This project delivers a comprehensive performance diagnostics platform for competitive chess players. Built as an internship showcase for a chess analytics firm, the pipeline collects live game archives from Chess.com's public REST API, performs in-depth statistical exploratory data analysis (EDA), generates 8 publication-grade visualization figures using **Matplotlib** and **Seaborn**, and compiles an interactive HTML dashboard using **Plotly**.

A built-in **Grandmaster-calibrated synthetic data engine** provides seamless offline fallback (~5,000 games) when API rate limits or network issues occur.

---

## 📁 Project Structure

```
project1_player_performance/
│
├── requirements.txt            # Python dependencies (pandas, matplotlib, seaborn, plotly, requests, numpy)
├── fetch_data.py               # Data Collection: Chess.com REST API parser & synthetic GM generator
├── analyze.py                  # EDA & 8 publication-quality Matplotlib/Seaborn dark-theme charts
├── dashboard.py                # Interactive Plotly executive dashboard (chess_dashboard.html)
├── main.py                     # Master pipeline orchestrator & CLI runner
├── README.md                   # Comprehensive project documentation
│
├── chess_games.csv             # Structured dataset of games (generated on run)
├── chess_dashboard.html        # Interactive HTML dashboard (generated on run)
└── output/                     # Publication-ready visualization charts (generated on run)
    ├── 01_opening_win_rates.png
    ├── 02_rating_trend.png
    ├── 03_time_of_day_performance.png
    ├── 04_game_duration_distribution.png
    ├── 05_win_rate_by_color.png
    ├── 06_monthly_games_played.png
    ├── 07_result_distribution.png
    └── 08_rating_vs_game_duration.png
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure Python 3.9+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Complete Pipeline
```bash
# Analyze default player (Hikaru Nakamura) using live API (with automatic synthetic fallback)
python main.py

# Or analyze any specific Chess.com player:
python main.py magnuscarlsen

# Or immediately generate ~5,000 realistic synthetic games (offline mode, no network delay):
python main.py --sample
```

---

## 📊 Modules & Architectural Overview

### 1. `fetch_data.py` — Data Collection & PGN Parsing
- **Live API Integration**: Queries `https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}` with RFC-compliant headers and rate-limit throttling.
- **PGN Header & Moves Extraction**:
  - `date`, `white_player`, `black_player`, `white_rating`, `black_rating`
  - `result` (Win / Loss / Draw for the target player)
  - `opening` and `eco_code` (parsed from `ECOUrl` and PGN tags)
  - `num_moves` (full move count extracted from PGN notation)
  - `time_control` and `termination` (resignation, checkmate, time forfeit, etc.)
- **Enriched Attributes**: Computes `player_color`, `player_rating`, `opponent_rating`, `time_of_day` (Morning, Afternoon, Evening, Night), and `day_of_week`.
- **Grandmaster Synthetic Engine (`generate_sample_data`)**:
  - Generates 5,000 realistic games simulating authentic GM Elo random walks (3100–3350).
  - Skewed opening distributions matching elite repertoire (Sicilian Najdorf, King's Indian, Queen's Gambit, etc.).
  - Real opponent handles (`MagnusCarlsen`, `DanielNaroditsky`, `Firouzja2003`, etc.).

### 2. `analyze.py` — Exploratory Data Analysis & Static Visualizations
Generates 8 publication-grade charts saved at 300 DPI in the `output/` folder using a custom dark chess aesthetic:
1. **01_opening_win_rates.png**: Horizontal stacked bar chart (Win: Emerald, Draw: Gray, Loss: Crimson) for top 15 openings with percentage labels and sample sizes.
2. **02_rating_trend.png**: Chronological rating progression with a 30-game moving average, annotated peak Elo, and lowest trough.
3. **03_time_of_day_performance.png**: Diurnal performance breakdown across Morning, Afternoon, Evening, and Night.
4. **04_game_duration_distribution.png**: Move count frequency histogram with Kernel Density Estimation (KDE), mean, and median markers.
5. **05_win_rate_by_color.png**: Dual donut charts illustrating White first-move advantage versus Black piece resilience.
6. **06_monthly_games_played.png**: Monthly game volume combined with a secondary axis win-rate trajectory line.
7. **07_result_distribution.png**: Modern donut chart showing career Win / Draw / Loss percentages with center summary KPI text.
8. **08_rating_vs_game_duration.png**: Scatter plot comparing opponent Elo against game duration (moves), grouped by outcome with regression trendline.

### 3. `dashboard.py` — Interactive Plotly HTML Dashboard
Creates `chess_dashboard.html` utilizing `plotly.graph_objects` and `make_subplots`:
- **Executive KPI Cards**: Live indicators for Career Win Rate %, Total Games Analyzed, Peak Elo Rating, and Most Played Opening.
- **Interactive Rating Trend**: Zoomable time-series with hover cards displaying game date, opponent, rating, and result.
- **Opening Win Rates Bar**: Stacked interactive bars displaying tactical conversion rates across top variations.
- **Performance Heatmap**: 2D matrix visualizing Win Rate % across Day-of-Week vs. Time-of-Day.
- **Move Distribution**: Interactive histogram of game lengths.
- **Color Share Donut**: Proportional breakdown of White vs. Black outcomes.
- **Standalone Responsive HTML**: Self-contained file that can be opened in any modern browser without web servers.

### 4. `main.py` — Pipeline CLI Runner
Orchestrates the workflow with formatted console logging, timestamps, execution time benchmarks, and progress indicators.

---

## 📈 Data Dictionary (`chess_games.csv`)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `date` | `YYYY-MM-DD` | Date when the game concluded |
| `timestamp` | `ISO 8601` | Full UTC timestamp of the game |
| `month_year` | `YYYY-MM` | Year and month for aggregation |
| `day_of_week` | `String` | Day of the week (Monday - Sunday) |
| `time_of_day` | `String` | Diurnal slot (Morning / Afternoon / Evening / Night) |
| `white_player` | `String` | Username of player with White pieces |
| `black_player` | `String` | Username of player with Black pieces |
| `white_rating` | `Integer` | White player Elo rating at match start |
| `black_rating` | `Integer` | Black player Elo rating at match start |
| `player_color` | `String` | Target player piece color (`White` or `Black`) |
| `player_rating`| `Integer` | Target player Elo rating |
| `opponent_player`| `String` | Opponent username |
| `opponent_rating`| `Integer`| Opponent Elo rating |
| `result` | `String` | Target player result (`win`, `loss`, `draw`) |
| `opening` | `String` | Standard chess opening name and variation |
| `eco_code` | `String` | Encyclopedia of Chess Openings (ECO) code (e.g. `B90`) |
| `num_moves` | `Integer` | Total full moves completed in the game |
| `time_control` | `String` | Time control format (e.g. `180+2`, `60+0`) |
| `termination` | `String` | Reason for game conclusion (`Resignation`, `Checkmate`, `Time forfeit`) |

---

## 💡 Internship Takeaways & Engineering Highlights

1. **Robust Error Handling**: The pipeline never fails due to network downtime; if Chess.com's API encounters rate limits (HTTP 429) or offline conditions, the Grandmaster synthetic fallback transparently activates.
2. **Production-Grade Visual Design**: Custom color theory applied with Emerald (`#10b981`), Crimson (`#ef4444`), and Chess Gold (`#f59e0b`) on dark slate card containers (`#151922`).
3. **Bilingual Documentation**: Code comments utilize a clear blend of English and Hindi (Hinglish) to facilitate onboarding across global engineering and analytics teams.
