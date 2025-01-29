import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

# Enable caching to avoid repeated API calls
@st.cache_data
def fetch_all_players(api_key):
    url = "https://api.football-data.org/v4/players"
    headers = {"X-Auth-Token": api_key}
    response = requests.get(url, headers=headers)
    
    # Debugging: Check the raw response from API
    if response.status_code == 200:
        players = response.json()
        # Print the structure for debugging
        st.write(players)  # Debugging output: Print response structure
        
        if 'players' in players:  # Assuming the response contains a 'players' key
            player_names = [player['name'] for player in players['players']]  # Adjust based on the response structure
            player_ids = [player['id'] for player in players['players']]  # Adjust based on the response structure
            return player_names, player_ids
        else:
            st.error("No 'players' key found in the response.")
            return [], []
    else:
        st.error("Failed to fetch players")
        return [], []

@st.cache_data
def fetch_player_data(player_id, api_key):
    url = f"https://api.football-data.org/v4/players/{player_id}"
    headers = {"X-Auth-Token": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data for player {player_id}")
        return {}

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

    # API key input
    api_key = st.sidebar.text_input("Enter API Key", type="password")

    if api_key:
        # Fetch all player names for autocomplete suggestions
        all_player_names, player_ids = fetch_all_players(api_key)

        # Player selection
        st.sidebar.header("Player Selection")
        player1_name = st.sidebar.selectbox("Select Player 1", all_player_names)
        player2_name = st.sidebar.selectbox("Select Player 2", all_player_names)

        # Find the player ids from the player names
        player1_id = player_ids[all_player_names.index(player1_name)]
        player2_id = player_ids[all_player_names.index(player2_name)]

        # Fetch player data
        player1_data = fetch_player_data(player1_id, api_key)
        player2_data = fetch_player_data(player2_id, api_key)

        # Metric selection
        st.sidebar.header("Metric Selection")
        metric_categories = {
            "Attacking": ["Goals", "Assists", "Shots", "xG"],
            "Defending": ["Tackles", "Interceptions", "Clearances"],
            "Passing": ["Passes Completed", "Key Passes", "Pass Accuracy"]
        }
        selected_category = st.sidebar.selectbox("Select Metric Category", list(metric_categories.keys()))
        selected_metrics = st.sidebar.multiselect("Select Metrics", metric_categories[selected_category])

        if player1_data and player2_data and selected_metrics:
            # Extract stats for the selected metrics
            player1_stats = [player1_data.get(metric.lower(), 0) for metric in selected_metrics]
            player2_stats = [player2_data.get(metric.lower(), 0) for metric in selected_metrics]

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
        st.warning("Please enter a valid API key.")

# Run the app
if __name__ == "__main__":
    main()
