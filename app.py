import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# Simulated list of player names (this would ideally come from a dynamic source like fbref or an API)
player_names_list = [
    "Lionel Messi", "Cristiano Ronaldo", "Alisson Becker", "Mohamed Salah", "Kevin De Bruyne", 
    "Virgil van Dijk", "Harry Kane", "Neymar", "Kylian Mbappé", "Robert Lewandowski", "Sadio Mane",
    "Paul Pogba", "Raheem Sterling", "Son Heung-min", "Gareth Bale", "Jack Grealish", "Luka Modrić",
    "Sergio Ramos", "Eden Hazard", "Romelu Lukaku", "Pierre-Emerick Aubameyang", "Erling Haaland"
]

# Function to fetch player data from fbref.com
@st.cache
def fetch_player_data(player_name):
    try:
        # URL for fbref.com search
        search_url = f"https://fbref.com/en/search/search.fcgi?search={player_name}"
        response = requests.get(search_url)
        response.raise_for_status()  # Ensure we catch HTTP errors

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Debug: Print the raw HTML to understand the structure
        # st.text(soup.prettify())  # Uncomment to see the HTML structure

        # Find the first player link in the search results
        search_item = soup.find("div", {"class": "search-item-name"})
        if not search_item:
            st.warning(f"Player '{player_name}' not found on fbref.com.")
            return None, None  # Return None for both data and image if player not found
        
        player_link = search_item.find("a")["href"]
        player_url = f"https://fbref.com{player_link}"

        # Fetch player stats page
        player_response = requests.get(player_url)
        player_response.raise_for_status()  # Catch potential network issues
        player_soup = BeautifulSoup(player_response.text, "html.parser")

        # Extract stats
        stats_table = player_soup.find("table", {"id": "scout_summary"})
        if not stats_table:
            st.warning(f"No stats found for player '{player_name}'.")
            return None, None  # Return None for both data and image if stats table not found

        stats = {}
        rows = stats_table.find_all("tr")
        for row in rows:
            cols = row.find_all(["th", "td"])
            if len(cols) == 2:
                stat_name = cols[0].text.strip()
                stat_value = cols[1].text.strip()
                stats[stat_name] = stat_value

        # Fetch player image
        image_tag = player_soup.find("img", {"class": "player-headshot"})
        player_image = image_tag["src"] if image_tag else None

        return stats, player_image

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {player_name}: {e}")
        return None, None  # Return None for both data and image on error


# Pizza chart function
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


# Radar chart function
def create_radar_chart(player1_data, player2_data, selected_metrics, players):
    df = pd.DataFrame({
        "Metric": selected_metrics * 2,
        "Value": player1_data + player2_data,
        "Player": [players[0]] * len(selected_metrics) + [players[1]] * len(selected_metrics)
    })
    fig = px.line_polar(df, r="Value", theta="Metric", color="Player", line_close=True, title="Radar Chart")
    fig.update_traces(fill='toself', line=dict(width=2))  # Customize line style
    st.plotly_chart(fig)


# Streamlit app
def main():
    st.title("Football Player Comparison Tool ⚽")
    st.write("Compare football players using pizza charts, radar charts, and a comparison table.")

    # Player search with autocomplete feature
    st.sidebar.header("Player Search")
    
    # Real-time suggestion for players' names
    player1_name_input = st.sidebar.text_input("Search Player 1")
    player2_name_input = st.sidebar.text_input("Search Player 2")
    
    # Filter the player names based on input
    filtered_player_names1 = [name for name in player_names_list if name.lower().startswith(player1_name_input.lower())]
    filtered_player_names2 = [name for name in player_names_list if name.lower().startswith(player2_name_input.lower())]
    
    # Provide suggestions based on input
    player1_name = st.sidebar.selectbox("Select Player 1", filtered_player_names1) if filtered_player_names1 else None
    player2_name = st.sidebar.selectbox("Select Player 2", filtered_player_names2) if filtered_player_names2 else None

    # Fetch player data
    player1_data, player1_image = fetch_player_data(player1_name) if player1_name else (None, None)
    player2_data, player2_image = fetch_player_data(player2_name) if player2_name else (None, None)

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

            # Display player images
            col1, col2 = st.columns(2)
            with col1:
                if player1_image:
                    st.image(player1_image, caption=player1_name, width=150)
                else:
                    st.warning(f"No image found for {player1_name}.")
            with col2:
                if player2_image:
                    st.image(player2_image, caption=player2_name, width=150)
                else:
                    st.warning(f"No image found for {player2_name}.")

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
