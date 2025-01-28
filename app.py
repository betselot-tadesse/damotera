import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# Function to fetch player data from fbref.com
@st.cache
def fetch_player_data(player_name):
    # URL for fbref.com search
    search_url = f"https://fbref.com/en/search/search.fcgi?search={player_name}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the first player link in the search results
    player_link = soup.find("div", {"class": "search-item-name"}).find("a")["href"]
    player_url = f"https://fbref.com{player_link}"

    # Fetch player stats page
    player_response = requests.get(player_url)
    player_soup = BeautifulSoup(player_response.text, "html.parser")

    # Extract stats (example: goals, assists, etc.)
    stats_table = player_soup.find("table", {"id": "scout_summary"})
    if not stats_table:
        return None

    stats = {}
    rows = stats_table.find_all("tr")
    for row in rows:
        cols = row.find_all(["th", "td"])
        if len(cols) == 2:
            stat_name = cols[0].text.strip()
            stat_value = cols[1].text.strip()
            stats[stat_name] = stat_value

    return stats

# Pizza chart function
def create_pizza_chart(stats, labels, title):
    num_stats = len(stats)
    angles = np.linspace(0, 2 * np.pi, num_stats, endpoint=False).tolist()
    stats += stats[:1]  # Close the circle
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, stats, color='red', alpha=0.25)
    ax.plot(angles, stats, color='red', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_title(title, size=14, y=1.1)
    st.pyplot(fig)

# Radar chart function
def create_radar_chart(player1_data, player2_data, selected_metrics, players):
    df = pd.DataFrame({
        "Metric": selected_metrics * 2,
        "Value": player1_data + player2_data,
        "Player": [players[0]] * len(selected_metrics) + [players[1]] * len(selected_metrics)
    })
    fig = px.line_polar(df, r="Value", theta="Metric", color="Player", line_close=True)
    st.plotly_chart(fig)

# Streamlit app
def main():
    st.title("Football Player Comparison Tool ⚽")
    st.write("Compare football players using pizza charts, radar charts, and a comparison table.")

    # Player search
    st.sidebar.header("Player Search")
    player1_name = st.sidebar.text_input("Search Player 1")
    player2_name = st.sidebar.text_input("Search Player 2")

    # Fetch player data
    player1_data = fetch_player_data(player1_name) if player1_name else None
    player2_data = fetch_player_data(player2_name) if player2_name else None

    if player1_data and player2_data:
        # Metric selection
        st.sidebar.header("Metric Selection")
        metric_categories = {
            "Attacking": ["Goals", "Assists", "Shots", "xG"],
            "Defending": ["Tackles", "Interceptions", "Clearances"],
            "Passing": ["Passes Completed", "Key Passes", "Pass Accuracy"]
        }
        selected_category = st.sidebar.selectbox("Select Metric Category", list(metric_categories.keys()))
        selected_metrics = st.sidebar.multiselect("Select Metrics", metric_categories[selected_category])

        if selected_metrics:
            # Extract selected metrics for both players
            player1_stats = [float(player1_data.get(metric, 0)) for metric in selected_metrics]
            player2_stats = [float(player2_data.get(metric, 0)) for metric in selected_metrics]

            # Normalize data for pizza chart
            max_values = [max(player1_stats[i], player2_stats[i]) for i in range(len(selected_metrics))]
            player1_normalized = [player1_stats[i] / max_values[i] * 100 for i in range(len(selected_metrics))]
            player2_normalized = [player2_stats[i] / max_values[i] * 100 for i in range(len(selected_metrics))]

            # Display pizza charts
            st.write(f"### {player1_name} vs {player2_name}")
            col1, col2 = st.columns(2)
            with col1:
                create_pizza_chart(player1_normalized, selected_metrics, player1_name)
            with col2:
                create_pizza_chart(player2_normalized, selected_metrics, player2_name)

            # Display radar chart
            st.write("### Radar Chart Comparison")
            create_radar_chart(player1_stats, player2_stats, selected_metrics, [player1_name, player2_name])

            # Display comparison table
            st.write("### Comparison Table")
            comparison_df = pd.DataFrame({
                "Metric": selected_metrics,
                player1_name: player1_stats,
                player2_name: player2_stats
            })
            st.table(comparison_df)
    else:
        st.warning("Please enter valid player names and ensure they exist on fbref.com.")

# Run the app
if __name__ == "__main__":
    main()
