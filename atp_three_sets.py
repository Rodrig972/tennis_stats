import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def get_atp_three_set_players_non_slam(season):
    file_path = f"Data_Base_Tennis/atp_{season}.db"
    try:
        conn = sqlite3.connect(file_path)
        query = """
        SELECT Winner, Loser
        FROM data
        WHERE (Series <> 'Grand Slam' AND Lsets = 1.0 AND Wsets = 2.0);
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Compter le nombre de fois où chaque joueur apparaît dans Winner ou Loser
        players = pd.concat([df["Winner"], df["Loser"]])
        top_players = players.value_counts().head(15).reset_index()
        top_players.columns = ["Joueur", "Nombre de matchs en 3 sets"]
        
        return top_players
    except sqlite3.Error:
        st.error(f"Base de données ATP {season} introuvable.")
        return pd.DataFrame()

def atp_three_set_non_slam_dashboard(season):
    st.title(f"Top 15 des joueurs avec le plus de matchs en 3 sets (hors Grand Chelem) - ATP {season}")
    data = get_atp_three_set_players_non_slam(season)
    if data.empty:
        st.warning("Aucune donnée trouvée.")
    else:
        st.dataframe(data)

# Pour exécuter sur Streamlit, appeler atp_three_set_non_slam_dashboard(saison)
