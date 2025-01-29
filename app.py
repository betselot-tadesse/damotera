import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

# Web scraping function to fetch player stats
def scrape_player_stats(player_url):
    # Send a request to the player URL
    response = requests.get(player_url)
    if response.status_code != 200:
        st.error("Failed to fetch player data")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Scrape player data (stats)
    player_data = {}
    
    # Example: Scraping stats from the 'Standard Stats' table (adjust based on actual table)
    stats_table = soup.find('table', {'class': 'stats_table'})
    if stats_table:
        headers = [th.get_text() for th in stats_table.find_all('th')]
        rows = stats_table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 1:
                stat_name = cols[0].get_text()
                stat_value = cols[1].get_text()  # This can vary based on table structure
                player_data[stat_name] = stat_value

    return player_data

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

    # Player selection
    st.sidebar.header("Player Selection")
    player1_name = st.sidebar.text_input("Enter Player 1 Name")
    player2_name = st.sidebar.text_input("Enter Player 2 Name")

    # URL for scraping player stats (Example URL for fbref.com)
    base_url = 'https://fbref.com/en/players/'
    player1_url = base_url + player1_name.replace(" ", "-")
    player2_url = base_url + player2_name.replace(" ", "-")

    # Scrape player data
    player1_data = scrape_player_stats(player1_url)
    player2_data = scrape_player_stats(player2_url)

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
            # Extract stats for the selected metrics
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
        st.warning("Failed to fetch data for one or both players. Please ensure the player names are correct.")

# Run the app
if __name__ == "__main__":
    main()
