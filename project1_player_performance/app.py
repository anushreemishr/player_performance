from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "chess_games.csv"
HTML_PATH = BASE_DIR / "chess_dashboard.html"

st.set_page_config(
    page_title="Chess Player Performance Analytics",
    page_icon="♟️",
    layout="wide",
)

st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #f8fafc; }
    [data-testid="stMetric"] {
        background: #151922; border: 1px solid #262f3f;
        padding: 16px; border-radius: 12px;
    }
    h1, h2, h3 { color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not CSV_PATH.exists():
        return None
    data = pd.read_csv(CSV_PATH)
    if "date" in data.columns:
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
    if "result" in data.columns:
        data["result"] = data["result"].astype(str).str.lower().str.strip()
    return data

df = load_data()

st.title("♟️ Chess Player Performance Analytics")
st.caption("An end-to-end data analytics project using Python, Pandas, Plotly and chess game data.")

if df is None or df.empty:
    st.error("Dataset not found or empty. Make sure chess_games.csv is in this same folder as app.py.")
    st.stop()

# Sidebar filters
st.sidebar.header("Explore the data")
results = sorted(df["result"].dropna().unique().tolist()) if "result" in df.columns else []
selected_results = st.sidebar.multiselect("Game result", results, default=results)

filtered = df.copy()
if "result" in filtered.columns and selected_results:
    filtered = filtered[filtered["result"].isin(selected_results)]

# KPIs
total_games = len(filtered)
wins = int((filtered["result"] == "win").sum()) if "result" in filtered.columns else 0
draws = int((filtered["result"] == "draw").sum()) if "result" in filtered.columns else 0
losses = int((filtered["result"] == "loss").sum()) if "result" in filtered.columns else 0
win_rate = (wins / total_games * 100) if total_games else 0
avg_rating = pd.to_numeric(filtered.get("player_rating", pd.Series(dtype=float)), errors="coerce").mean()
peak_rating = pd.to_numeric(filtered.get("player_rating", pd.Series(dtype=float)), errors="coerce").max()

st.subheader("Performance overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Games", f"{total_games:,}")
c2.metric("Wins", f"{wins:,}")
c3.metric("Win rate", f"{win_rate:.1f}%")
c4.metric("Average rating", f"{avg_rating:,.0f}" if pd.notna(avg_rating) else "N/A")
c5.metric("Peak rating", f"{peak_rating:,.0f}" if pd.notna(peak_rating) else "N/A")

overview, dashboard, data_tab, about = st.tabs(
    ["Overview", "Interactive dashboard", "Dataset", "About project"]
)

with overview:
    left, right = st.columns(2)
    with left:
        st.markdown("### Game outcomes")
        if total_games:
            outcome_counts = filtered["result"].value_counts().rename_axis("Result").reset_index(name="Games")
            st.bar_chart(outcome_counts.set_index("Result"))
    with right:
        st.markdown("### Performance by playing color")
        if {"player_color", "result"}.issubset(filtered.columns):
            color_perf = (
                filtered.assign(is_win=filtered["result"].eq("win"))
                .groupby("player_color", as_index=False)["is_win"].mean()
            )
            color_perf["Win rate (%)"] = color_perf["is_win"] * 100
            st.bar_chart(color_perf.set_index("player_color")["Win rate (%)"])
    st.markdown("### Most played openings")
    if "opening" in filtered.columns:
        st.bar_chart(filtered["opening"].value_counts().head(10))

with dashboard:
    st.markdown("### Existing Plotly dashboard")
    st.caption("This embeds the interactive HTML dashboard already present in your GitHub project.")
    if HTML_PATH.exists():
        html = HTML_PATH.read_text(encoding="utf-8")
        components.html(html, height=1500, scrolling=True)
    else:
        st.warning("chess_dashboard.html was not found. Add it beside app.py to show the original dashboard.")

with data_tab:
    st.markdown("### Chess games dataset")
    st.write(f"Showing {len(filtered):,} filtered records out of {len(df):,} total records.")
    st.dataframe(filtered, use_container_width=True, height=500)
    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="chess_games_filtered.csv",
        mime="text/csv",
    )

with about:
    st.markdown("""
    ### Project objective
    Analyze chess game history to understand player performance, rating progression,
    opening effectiveness, game outcomes, playing color, and game duration.

    ### Analytics workflow
    1. Collect chess game records.
    2. Clean and prepare data using Python and Pandas.
    3. Perform exploratory data analysis.
    4. Create visualizations using Matplotlib, Seaborn and Plotly.
    5. Present the results in an interactive dashboard.

    ### Technology stack
    - Python and Pandas
    - NumPy
    - Matplotlib and Seaborn
    - Plotly
    - Streamlit
    - CSV dataset
    """)

st.divider()
st.caption("Chess Player Performance Analytics | Built with Python and Streamlit")
