"""
=============================================================================
Module: fetch_data.py
Project: Chess Player Performance Analytics Dashboard
Author: Data Analyst Intern
Description:
    Yeh module Chess.com public API se real games fetch karta hai.
    Agar network ya API issues ho, toh yeh realistic synthetic data (~5000 games)
    generate karke seamlessly fallback provide karta hai.
    Data clean karke CSV file (chess_games.csv) me save kiya jata hai.
=============================================================================
"""

import os
import re
import sys
import time
import random
import argparse
import datetime
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
import requests

# ---------------------------------------------------------------------------
# Global Constants & Headers
# ---------------------------------------------------------------------------
CHESS_COM_API_BASE = "https://api.chess.com/pub"
DEFAULT_USER_AGENT = "ChessDataAnalystIntern/1.0 (contact: intern@chessanalytics.org)"
DEFAULT_OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chess_games.csv")

# Chess openings repository with standard ECO codes
REALISTIC_OPENINGS = [
    ("Sicilian Defense: Najdorf Variation", "B90"),
    ("Sicilian Defense: Dragon Variation", "B70"),
    ("Sicilian Defense: Classical Variation", "B56"),
    ("Sicilian Defense: Alapin Variation", "B22"),
    ("Ruy Lopez: Berlin Defense", "C65"),
    ("Ruy Lopez: Closed Variation", "C84"),
    ("Ruy Lopez: Marshall Attack", "C89"),
    ("Queen's Gambit Declined: Traditional", "D30"),
    ("Queen's Gambit Declined: Tartakower", "D58"),
    ("Queen's Gambit Accepted", "D20"),
    ("King's Indian Defense: Classical", "E90"),
    ("King's Indian Defense: Mar del Plata", "E97"),
    ("Caro-Kann Defense: Advance Variation", "B12"),
    ("Caro-Kann Defense: Classical", "B18"),
    ("French Defense: Winawer Variation", "C15"),
    ("French Defense: Advance Variation", "C02"),
    ("English Opening: Symmetrical", "A30"),
    ("Italian Game: Giuoco Piano", "C50"),
    ("Nimzo-Indian Defense: Rubinstein", "E40"),
    ("London System", "D02"),
    ("Grunfeld Defense: Russian Variation", "D96"),
    ("Scandinavian Defense: Modern", "B01"),
    ("Reti Opening: King's Indian Attack", "A07"),
    ("King's Gambit: Accepted", "C34"),
    ("Vienna Game: Vienna Gambit", "C29"),
    ("Modern Defense: Standard", "B06"),
    ("Catalan Opening: Closed", "E06"),
    ("Slav Defense: Exchange", "D10"),
]

REALISTIC_OPPONENTS = [
    ("MagnusCarlsen", 3280),
    ("DanielNaroditsky", 3210),
    ("Firouzja2003", 3240),
    ("AndrewTang", 3190),
    ("nihalsarin", 3205),
    ("FabianoCaruana", 3185),
    ("Praggchess", 3175),
    ("ErigaisiArjun", 3215),
    ("viditchess", 3150),
    ("Nepomniachtchi", 3220),
    ("Grischuk", 3165),
    ("So", 3200),
    ("HansMokeNiemann", 3140),
    ("JeffreyXiong", 3125),
    ("Danya", 3205),
    ("LevonAronian", 3180),
    ("AnishGiri", 3170),
    ("JanKrzysztofDuda", 3160),
    ("RayRobson", 3130),
    ("ShakhriyarMamedyarov", 3155),
]


# ---------------------------------------------------------------------------
# Helper Functions: PGN Parsing & Data Enrichment
# ---------------------------------------------------------------------------
def parse_pgn_headers(pgn_text: str) -> Dict[str, str]:
    """
    PGN text me se standard tags parse karta hai (e.g. ECO, ECOUrl, Date, Termination).
    """
    headers = {}
    if not pgn_text:
        return headers
    
    # Regex se saare [Key "Value"] pairs extract karte hain
    matches = re.findall(r'\[(\w+)\s+"([^"]*)"\]', pgn_text)
    for key, value in matches:
        headers[key] = value
    return headers


def extract_move_count(pgn_text: str) -> int:
    """
    PGN moves text se full moves count calculate karta hai.
    """
    if not pgn_text:
        return random.randint(28, 55)
    
    move_matches = re.findall(r'(\d+)\.\s', pgn_text)
    if move_matches:
        try:
            return max(int(m) for m in move_matches)
        except ValueError:
            return 38
    return 38


def derive_time_of_day(hour: int) -> str:
    """
    Hour ke basis par Time of Day category assign karta hai:
    Morning (06:00 - 11:59)
    Afternoon (12:00 - 16:59)
    Evening (17:00 - 20:59)
    Night (21:00 - 05:59)
    """
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"


def clean_opening_name(ecourl: Optional[str], default_eco: str = "A00") -> Tuple[str, str]:
    """
    ECOUrl string se clean human-readable opening name aur ECO code extract karta hai.
    Example: https://www.chess.com/openings/Sicilian-Defense-Najdorf-Variation
    """
    if ecourl and "/openings/" in ecourl:
        slug = ecourl.split("/openings/")[-1].replace("-", " ")
        # Variation se pehle ka standard name
        opening_name = slug.strip().title()
        return opening_name, default_eco
    
    # Fallback to random realistic opening
    return "Sicilian Defense: Najdorf Variation", "B90"


# ---------------------------------------------------------------------------
# Real Chess.com API Data Fetching
# ---------------------------------------------------------------------------
def fetch_player_monthly_archives(username: str, months_count: int = 4) -> List[str]:
    """
    Chess.com API se player ke game archives urls ki list fetch karta hai.
    """
    url = f"{CHESS_COM_API_BASE}/player/{username.lower()}/games/archives"
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    
    print(f"[*] Fetching archive list for player '{username}' from Chess.com...")
    response = requests.get(url, headers=headers, timeout=12)
    response.raise_for_status()
    
    archives = response.json().get("archives", [])
    if not archives:
        print("[!] Koi archives nahi mile.")
        return []
    
    # Recent months select karte hain
    recent_archives = archives[-months_count:] if len(archives) >= months_count else archives
    print(f"[+] Found {len(archives)} total archives. Selecting last {len(recent_archives)} months.")
    return recent_archives


def fetch_games_from_archive(archive_url: str) -> List[Dict[str, Any]]:
    """
    Ek specific monthly archive URL se sabhi games download karta hai.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        res = requests.get(archive_url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get("games", [])
        elif res.status_code == 429:
            print("[!] Rate limited by Chess.com API. Pausing for 3 seconds...")
            time.sleep(3)
            res = requests.get(archive_url, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.json().get("games", [])
    except Exception as e:
        print(f"[-] Error fetching archive {archive_url}: {e}")
    return []


def parse_chess_com_game(game: Dict[str, Any], target_user: str) -> Optional[Dict[str, Any]]:
    """
    Chess.com game JSON object ko clean standard row structure me convert karta hai.
    """
    try:
        white_data = game.get("white", {})
        black_data = game.get("black", {})
        
        white_player = white_data.get("username", "Unknown")
        black_player = black_data.get("username", "Unknown")
        white_rating = int(white_data.get("rating", 1500))
        black_rating = int(black_data.get("rating", 1500))
        
        # Player color determine karte hain
        is_white = white_player.lower() == target_user.lower()
        player_color = "White" if is_white else "Black"
        player_rating = white_rating if is_white else black_rating
        opponent_player = black_player if is_white else white_player
        opponent_rating = black_rating if is_white else white_rating
        
        # Result mapping
        white_result_raw = white_data.get("result", "")
        black_result_raw = black_data.get("result", "")
        player_result_raw = white_result_raw if is_white else black_result_raw
        
        win_codes = {"win"}
        draw_codes = {"agreed", "repetition", "stalemate", "insufficient", "50move", "timevsinsufficient"}
        
        if player_result_raw in win_codes:
            player_result = "win"
        elif player_result_raw in draw_codes:
            player_result = "draw"
        else:
            player_result = "loss"
            
        # PGN and Headers extraction
        pgn_text = game.get("pgn", "")
        headers = parse_pgn_headers(pgn_text)
        
        # Date & Time calculation
        end_time_ts = game.get("end_time")
        if end_time_ts:
            dt = datetime.datetime.fromtimestamp(end_time_ts, tz=datetime.timezone.utc)
        else:
            date_str = headers.get("Date", "2024.01.01").replace(".", "-")
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
        date_formatted = dt.strftime("%Y-%m-%d")
        time_of_day = derive_time_of_day(dt.hour)
        day_of_week = dt.strftime("%A")
        month_year = dt.strftime("%Y-%m")
        
        # Opening details
        eco_code = headers.get("ECO", "A00")
        ecourl = headers.get("ECOUrl")
        opening_name, _ = clean_opening_name(ecourl, eco_code)
        if "Opening" in headers and headers["Opening"]:
            opening_name = headers["Opening"]
            
        # Move count & termination
        num_moves = extract_move_count(pgn_text)
        time_control = game.get("time_control", "180+2")
        termination = headers.get("Termination", "Normal")
        
        # Clean termination message
        if "resignation" in termination.lower():
            clean_term = "Resignation"
        elif "checkmate" in termination.lower():
            clean_term = "Checkmate"
        elif "time" in termination.lower():
            clean_term = "Time forfeit"
        elif "agreed" in termination.lower():
            clean_term = "Draw by agreement"
        elif "repetition" in termination.lower():
            clean_term = "Draw by repetition"
        elif "stalemate" in termination.lower():
            clean_term = "Draw by stalemate"
        else:
            clean_term = termination.split("won by")[-1].strip().capitalize() if "won by" in termination else "Normal"
            
        return {
            "date": date_formatted,
            "timestamp": dt.isoformat(),
            "month_year": month_year,
            "day_of_week": day_of_week,
            "time_of_day": time_of_day,
            "white_player": white_player,
            "black_player": black_player,
            "white_rating": white_rating,
            "black_rating": black_rating,
            "player_color": player_color,
            "player_rating": player_rating,
            "opponent_player": opponent_player,
            "opponent_rating": opponent_rating,
            "result": player_result,  # 'win', 'loss', 'draw' for the target player
            "opening": opening_name,
            "eco_code": eco_code,
            "num_moves": num_moves,
            "time_control": time_control,
            "termination": clean_term,
        }
    except Exception as e:
        # Koi single game corrupted ho toh skip karte hain
        return None


def fetch_real_data(username: str = "hikaru", months_count: int = 4, max_games: int = 5000) -> pd.DataFrame:
    """
    Chess.com API se target player ke games fetch karta hai.
    Data clean karke DataFrame return karta hai.
    """
    print(f"\n=======================================================")
    print(f"[+] Starting Chess.com API Data Fetch for: {username}")
    print(f"=======================================================")
    
    archives = fetch_player_monthly_archives(username, months_count=months_count)
    if not archives:
        raise ValueError("No archives returned from Chess.com API.")
        
    all_parsed_games: List[Dict[str, Any]] = []
    
    for idx, archive_url in enumerate(archives, 1):
        print(f"[*] Downloading games from archive [{idx}/{len(archives)}]: {archive_url}...")
        raw_games = fetch_games_from_archive(archive_url)
        print(f"    -> Retrieved {len(raw_games)} games.")
        
        for g in raw_games:
            # Only chess standard rules
            if g.get("rules", "chess") == "chess":
                row = parse_chess_com_game(g, username)
                if row:
                    all_parsed_games.append(row)
                    
            if len(all_parsed_games) >= max_games:
                print(f"[!] Target limit of {max_games} games reached.")
                break
                
        if len(all_parsed_games) >= max_games:
            break
            
        time.sleep(0.5)  # API etiquette rate limiting
        
    if not all_parsed_games:
        raise ValueError("No valid games could be parsed from the archives.")
        
    df = pd.DataFrame(all_parsed_games)
    print(f"\n[OK] Successfully fetched and parsed {len(df)} real games from Chess.com API!")
    return df


# ---------------------------------------------------------------------------
# Synthetic Realistic Data Generator (Fallback & Offline Mode)
# ---------------------------------------------------------------------------
def generate_sample_data(num_games: int = 5000, username: str = "hikaru") -> pd.DataFrame:
    """
    Realistic synthetic chess games dataset generate karta hai (~5000 games).
    Grandmaster-level metrics, realistic rating random walks, opening distributions,
    aur authentic game outcomes simulate karta hai.
    """
    print(f"\n=======================================================")
    print(f"[*] Generating {num_games} Realistic Synthetic Games for '{username}'...")
    print(f"=======================================================")
    
    np.random.seed(42)
    random.seed(42)
    
    # 1. Date Range: Last 365 days
    end_date = datetime.date(2024, 11, 20)
    start_date = end_date - datetime.timedelta(days=365)
    total_days = (end_date - start_date).days
    
    # Generate dates with weekend and evening clustering
    game_dates = []
    for _ in range(num_games):
        day_offset = random.randint(0, total_days)
        game_d = start_date + datetime.timedelta(days=day_offset)
        
        # Hikaru streams often in evening/night
        hour_weights = [1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 21, 15, 8]
        hour = random.choices(range(24), weights=hour_weights)[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        dt = datetime.datetime.combine(game_d, datetime.time(hour, minute, second))
        game_dates.append(dt)
        
    game_dates.sort()  # Sort chronologically for realistic rating graph
    
    # 2. Rating Simulation (Mean-reverting Random Walk around 3220)
    base_rating = 3200.0
    current_rating = base_rating
    player_ratings = []
    
    for _ in range(num_games):
        reversion_pull = (base_rating - current_rating) * 0.05
        step = np.random.normal(0, 6.0) + reversion_pull
        current_rating += step
        current_rating = max(3110.0, min(3345.0, current_rating))
        player_ratings.append(int(round(current_rating)))
        
    # 3. Time controls distribution
    time_control_choices = ["180+0", "180+2", "60+0", "60+1", "300+0", "120+1"]
    time_control_weights = [0.45, 0.25, 0.15, 0.08, 0.05, 0.02]
    
    # 4. Opening frequencies (skewed towards popular Hikaru openings)
    opening_weights = [
        0.14, 0.09, 0.07, 0.05, 0.08, 0.06, 0.04, 0.07, 0.05, 0.04,
        0.06, 0.04, 0.05, 0.03, 0.04, 0.02, 0.03, 0.05, 0.04, 0.03,
        0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01
    ]
    # Normalize weights to sum to 1
    total_w = sum(opening_weights)
    opening_weights = [w / total_w for w in opening_weights]
    
    terminations_win = ["Resignation", "Checkmate", "Time forfeit"]
    terminations_win_w = [0.55, 0.25, 0.20]
    
    terminations_loss = ["Resignation", "Checkmate", "Time forfeit"]
    terminations_loss_w = [0.50, 0.15, 0.35]
    
    terminations_draw = ["Draw by agreement", "Draw by repetition", "Draw by stalemate", "Draw by insufficient material"]
    terminations_draw_w = [0.40, 0.38, 0.12, 0.10]
    
    games_list = []
    
    for i in range(num_games):
        dt = game_dates[i]
        p_rating = player_ratings[i]
        
        # Color distribution (~50% White, ~50% Black)
        is_white = (i % 2 == random.choice([0, 1]))
        player_color = "White" if is_white else "Black"
        
        # Opponent selection
        opp_name, opp_base_rating = random.choice(REALISTIC_OPPONENTS)
        opp_rating = int(round(opp_base_rating + np.random.normal(0, 35)))
        opp_rating = max(2950, min(3320, opp_rating))
        
        white_player = username if is_white else opp_name
        black_player = opp_name if is_white else username
        white_rating = p_rating if is_white else opp_rating
        black_rating = opp_rating if is_white else p_rating
        
        # Win rate probability logic based on Elo & Color
        rating_diff = p_rating - opp_rating
        # Base win probability for Grandmaster Hikaru is high (~70%)
        color_bonus = 0.04 if is_white else -0.04
        expected_win_prob = 1.0 / (1.0 + 10 ** (-rating_diff / 400.0))
        win_prob = 0.50 + 0.35 * (expected_win_prob - 0.5) + color_bonus + 0.16
        win_prob = max(0.40, min(0.85, win_prob))
        
        draw_prob = 0.18 + 0.04 * (1.0 - abs(expected_win_prob - 0.5))
        loss_prob = max(0.05, 1.0 - (win_prob + draw_prob))
        
        # Normalize
        s = win_prob + draw_prob + loss_prob
        win_prob /= s
        draw_prob /= s
        loss_prob /= s
        
        outcome = random.choices(["win", "draw", "loss"], weights=[win_prob, draw_prob, loss_prob])[0]
        
        # Move count logic (Wins & Draws tend to last differently)
        if outcome == "draw":
            num_moves = int(np.random.normal(48, 14))
            term = random.choices(terminations_draw, weights=terminations_draw_w)[0]
        elif outcome == "win":
            num_moves = int(np.random.normal(38, 12))
            term = random.choices(terminations_win, weights=terminations_win_w)[0]
        else:
            num_moves = int(np.random.normal(36, 11))
            term = random.choices(terminations_loss, weights=terminations_loss_w)[0]
            
        num_moves = max(10, min(115, num_moves))
        
        # Select opening
        opening_tuple = random.choices(REALISTIC_OPENINGS, weights=opening_weights)[0]
        opening_name, eco_code = opening_tuple
        
        # Time control
        tc = random.choices(time_control_choices, weights=time_control_weights)[0]
        
        games_list.append({
            "date": dt.strftime("%Y-%m-%d"),
            "timestamp": dt.isoformat(),
            "month_year": dt.strftime("%Y-%m"),
            "day_of_week": dt.strftime("%A"),
            "time_of_day": derive_time_of_day(dt.hour),
            "white_player": white_player,
            "black_player": black_player,
            "white_rating": white_rating,
            "black_rating": black_rating,
            "player_color": player_color,
            "player_rating": p_rating,
            "opponent_player": opp_name,
            "opponent_rating": opp_rating,
            "result": outcome,
            "opening": opening_name,
            "eco_code": eco_code,
            "num_moves": num_moves,
            "time_control": tc,
            "termination": term,
        })
        
    df = pd.DataFrame(games_list)
    print(f"[OK] Generated {len(df)} synthetic games successfully with realistic GM distributions.")
    return df


# ---------------------------------------------------------------------------
# Main Orchestrator for Data Fetching & Saving
# ---------------------------------------------------------------------------
def collect_and_save_data(username: str = "hikaru",
                          output_path: str = DEFAULT_OUTPUT_CSV,
                          force_sample: bool = False,
                          months: int = 4,
                          sample_size: int = 5000) -> pd.DataFrame:
    """
    Chess data collect karta hai (real API first, failsafe synthetic data fallback)
    aur structured CSV format me save karta hai.
    """
    df = None
    
    if not force_sample:
        try:
            print(f"[*] Attempting to fetch real data for '{username}'...")
            df = fetch_real_data(username=username, months_count=months, max_games=sample_size)
            if len(df) < 50:
                print(f"[!] Sirf {len(df)} games mile. Dataset enrichment ke liye synthetic generator use karenge.")
                df = generate_sample_data(num_games=sample_size, username=username)
        except Exception as e:
            print(f"[-] Real API Fetch Failed: {e}")
            print("[*] Switching to robust synthetic GM data generator fallback...")
            df = generate_sample_data(num_games=sample_size, username=username)
    else:
        print("[*] Force sample mode active. Generating synthetic dataset...")
        df = generate_sample_data(num_games=sample_size, username=username)
        
    # Directory creation agar exist na kare
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\n[SUCCESS] Dataset successfully saved to: {output_path}")
    print(f"    - Total Games: {len(df)}")
    print(f"    - Target Player: {username}")
    print(f"    - Overall Win Rate: {(df['result'] == 'win').mean() * 100:.2f}%")
    print(f"    - Date Range: {df['date'].min()} to {df['date'].max()}\n")
    return df


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Fetch Chess.com player game data or generate realistic synthetic games.")
    parser.add_argument("username", nargs="?", default="hikaru", help="Chess.com username (default: 'hikaru')")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_CSV, help="Output CSV path")
    parser.add_argument("--sample", "-s", action="store_true", help="Directly generate realistic sample dataset")
    parser.add_argument("--months", "-m", type=int, default=4, help="Number of monthly archives to fetch from API")
    parser.add_argument("--games", "-g", type=int, default=5000, help="Number of games to generate if using sample data")
    
    args = parser.parse_args()
    collect_and_save_data(
        username=args.username,
        output_path=args.output,
        force_sample=args.sample,
        months=args.months,
        sample_size=args.games
    )


if __name__ == "__main__":
    main()
