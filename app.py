import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

# Enable caching to avoid repeated scraping
@st.cache_data
def fetch_all_players():
    base_url = "https://fbref.com/en/players/"
    player_names = []
    player_urls = []
    
    page_number = 1
    while True:
        url = f"{base_url}{page_number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        player_table = soup.find("table", {"class": "stats_table"})
        if not player_table:
            break
        
        rows = player_table.find_all("tr")
        for row in rows[1:]:  # Skip header row
            cols = row.find_all("td")
            if len(cols) > 1:
                player_name = cols[0].get_text(strip=True)
                player_link = "https://fbref.com" + cols[0].find("a")["href"]
                player_names.append(player_name)
                player_urls.append(player_link)
        
        # Check if there's a next page
        next_page = soup.find("a", text="Next Page")
        if not next_page:
            break
        page_number += 1
    
    return player_names, player_urls


@st.cache_data
def fetch_player_data(player_url):
    response = requests.get(player_url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    stats = {}
    
    # Extract basic info
    info_section = soup.find("div", {"id": "info"})
    if info_section:
        stats["Name"] = info_section.find("h1").get_text(strip=True)
        stats["Position"] = info_section.find("strong", text="Position:").find_next().get_text(strip=True)
    
    # Extract detailed stats from all tables
    for table in soup.find_all("table", {"class": "stats_table"}):
        table_id = table.get("id")
        if table_id:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all(["th", "td"])
                if len(cols) == 2:
                    stat_name = cols[0].text.strip()
                    stat_value = cols[1].text.strip()
                    stats[f"{table_id}_{stat_name}"] = stat_value
    
    return stats


def create_pizza_chart(stats, labels, title):
    num_stats = len(stats)
    angles = np.linspace(0, 2 * np.pi, num_stats, endpoint=False).tolist()
    stats += stats[:1]  # Close the circle
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, stats, color='lightblue', alpha=0.5)
    ax.plot(angles, stats, color='blue', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, rotation=45)
    ax.set_title(title, size=14, y=1.1)
    st.pyplot(fig)


def create_radar_chart(player1_data, player2_data, selected_metrics, players):
    df = pd.DataFrame({
        "Metric": selected_metrics * 2,
        "Value": player1_data + player2_data,
        "Player": [players[0]] * len(selected_metrics) + [players[1]] * len(selected_metrics)
    })
    fig = px.line_polar(df, r="Value", theta="Metric", color="Player", line_close=True, title="Radar Chart")
    fig.update_traces(fill='toself', line=dict(width=2))  # Customize line style
    st.plotly_chart(fig)


def main():
    st.title("Football Player Comparison Tool ⚽")
    st.write("Compare football players using pizza charts, radar charts, and a comparison table.")

    # Fetch all player names for autocomplete suggestions
    all_player_names, player_urls = fetch_all_players()

    # Search for players with real-time suggestions
    st.sidebar.header("Player Search")

    # Player 1 search and suggestions
    player1_name_input = st.sidebar.text_input("Search Player 1", key="player1_search")
    if player1_name_input:
        filtered_player_names1 = [name for name in all_player_names if player1_name_input.lower() in name.lower()]
        if filtered_player_names1:
            player1_name = st.sidebar.selectbox("Select Player 1", filtered_player_names1, key="player1_select")
        else:
            st.sidebar.warning("No matching players found.")
            player1_name = None
    else:
        player1_name = None

    # Player 2 search and suggestions
    player2_name_input = st.sidebar.text_input("Search Player 2", key="player2_search")
    if player2_name_input:
        filtered_player_names2 = [name for name in all_player_names if player2_name_input.lower() in name.lower()]
        if filtered_player_names2:
            player2_name = st.sidebar.selectbox("Select Player 2", filtered_player_names2, key="player2_select")
        else:
            st.sidebar.warning("No matching players found.")
            player2_name = None
    else:
        player2_name = None

    # Get player URLs for the selected players
    player1_url = player_urls[all_player_names.index(player1_name)] if player1_name else None
    player2_url = player_urls[all_player_names.index(player2_name)] if player2_name else None

    # Fetch player data
    player1_data = fetch_player_data(player1_url) if player1_url else {}
    player2_data = fetch_player_data(player2_url) if player2_url else {}

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
