import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def get_top_wta_three_set_players(season):
    file_path = f"Data_Base_Tennis/wta_{season}.db"
    try:
        conn = sqlite3.connect(file_path)
        query = """
        SELECT Winner, Loser
        FROM data
        WHERE (Lsets = 1.0 AND Wsets = 2.0);
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Compter le nombre de fois où chaque joueuse apparaît dans Winner ou Loser
        players = pd.concat([df["Winner"], df["Loser"]])
        top_players = players.value_counts().head(15).reset_index()
        top_players.columns = ["Joueuse", "Nombre de matchs en 3 sets"]
        
        return top_players
    except sqlite3.Error:
        st.error(f"Base de données WTA {season} introuvable.")
        return pd.DataFrame()

def wta_three_set_dashboard(season):
    st.title(f"Top 15 des joueuses avec le plus de matchs en 3 sets - WTA {season}")
    data = get_top_wta_three_set_players(season)
    if data.empty:
        st.warning("Aucune donnée trouvée.")
    else:
        st.dataframe(data)

# Pour exécuter sur Streamlit, appeler wta_three_set_dashboard(saison)
