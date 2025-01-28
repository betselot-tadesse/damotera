import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px

# Load data (replace this with your dataset or scraping logic)
@st.cache
def load_data():
    # Example dataset (replace with actual data from fbref.com)
    data = {
        "Player": ["Mohamed Salah", "Kevin De Bruyne", "Virgil van Dijk", "Harry Kane"],
        "Goals": [22, 10, 2, 20],
        "Assists": [12, 15, 1, 10],
        "Shots": [110, 80, 10, 120],
        "xG": [18.5, 8.2, 1.5, 19.0],
        "Tackles": [15, 20, 50, 10],
        "Interceptions": [10, 12, 40, 8],
        "Clearances": [5, 8, 100, 6],
        "Passes Completed": [800, 1200, 700, 900],
        "Key Passes": [60, 90, 10, 50],
        "Pass Accuracy": [85, 89, 92, 88]
    }
    return pd.DataFrame(data)

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

    # Load data
    data = load_data()

    # Player selection
    st.sidebar.header("Player Selection")
    player1 = st.sidebar.selectbox("Select Player 1", data['Player'].unique())
    player2 = st.sidebar.selectbox("Select Player 2", data['Player'].unique())

    # Metric selection
    st.sidebar.header("Metric Selection")
    metric_categories = {
        "Attacking": ["Goals", "Assists", "Shots", "xG"],
        "Defending": ["Tackles", "Interceptions", "Clearances"],
        "Passing": ["Passes Completed", "Key Passes", "Pass Accuracy"]
    }
    selected_category = st.sidebar.selectbox("Select Metric Category", list(metric_categories.keys()))
    selected_metrics = st.sidebar.multiselect("Select Metrics", metric_categories[selected_category])

    if player1 and player2 and selected_metrics:
        # Filter data for selected players and metrics
        player1_data = data[data['Player'] == player1][selected_metrics].iloc[0].tolist()
        player2_data = data[data['Player'] == player2][selected_metrics].iloc[0].tolist()

        # Normalize data for pizza chart
        max_values = [max(player1_data[i], player2_data[i]) for i in range(len(selected_metrics))]
        player1_normalized = [player1_data[i] / max_values[i] * 100 for i in range(len(selected_metrics))]
        player2_normalized = [player2_data[i] / max_values[i] * 100 for i in range(len(selected_metrics))]

        # Display pizza charts
        st.write(f"### {player1} vs {player2}")
        col1, col2 = st.columns(2)
        with col1:
            create_pizza_chart(player1_normalized, selected_metrics, player1)
        with col2:
            create_pizza_chart(player2_normalized, selected_metrics, player2)

        # Display radar chart
        st.write("### Radar Chart Comparison")
        create_radar_chart(player1_data, player2_data, selected_metrics, [player1, player2])

        # Display comparison table
        st.write("### Comparison Table")
        comparison_df = pd.DataFrame({
            "Metric": selected_metrics,
            player1: player1_data,
            player2: player2_data
        })
        st.table(comparison_df)

# Run the app
if __name__ == "__main__":
    main()
