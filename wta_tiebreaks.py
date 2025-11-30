import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def get_top_tiebreak_players(season, db_type="wta"):
    file_path = f"Data_Base_Tennis/{db_type}_{season}.db"
    try:
        conn = sqlite3.connect(file_path)
        query = """
        SELECT Series, Tournament, Surface, Date, Round, Winner, Loser, L1, W1, L2, W2, L3, W3
        FROM data 
        WHERE (L1 + W1 = 13 OR L2 + W2 = 13 OR L3 + W3 = 13);
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Compter le nombre de fois où chaque joueur apparaît dans Winner ou Loser
        players = pd.concat([df["Winner"], df["Loser"]])
        top_players = players.value_counts().head(15).reset_index()
        top_players.columns = ["Joueur", "Nombre de matchs avec tie-break"]
        
        return top_players, df
    except sqlite3.Error:
        st.error(f"Base de données {db_type.upper()} {season} introuvable.")
        return pd.DataFrame(), pd.DataFrame()

def get_player_tiebreak_percentage(player_name, df):
    # Filtrer les matchs où le joueur est impliqué
    player_matches = df[(df["Winner"] == player_name) | (df["Loser"] == player_name)]
    total_matches = len(player_matches)
    
    # Compter les matchs avec au moins un tie-break
    tiebreak_matches = player_matches[
        ((player_matches["W1"] == 7.0) & (player_matches["L1"] == 6.0)) |
        ((player_matches["W1"] == 6.0) & (player_matches["L1"] == 7.0)) |
        ((player_matches["W2"] == 7.0) & (player_matches["L2"] == 6.0)) |
        ((player_matches["W2"] == 6.0) & (player_matches["L2"] == 7.0)) |
        ((player_matches["W3"] == 7.0) & (player_matches["L3"] == 6.0)) |
        ((player_matches["W3"] == 6.0) & (player_matches["L3"] == 7.0))
    ]
    
    if total_matches > 0:
        percentage = (len(tiebreak_matches) / total_matches) * 100
        return percentage
    else:
        return 0

def tiebreak_dashboard(season, db_type="wta"):
    st.title(f"Top 15 des joueurs avec le plus de matchs avec tie-break - {db_type.upper()} {season}")
    top_players, df = get_top_tiebreak_players(season, db_type)
    
    if top_players.empty:
        st.warning("Aucune donnée trouvée.")
    else:
        st.dataframe(top_players)
    
    st.title("Pourcentage de matchs avec tie-break pour un joueur")
    player_name = st.text_input("Entrez le nom du joueur :")
    
    if player_name:
        percentage = get_player_tiebreak_percentage(player_name, df)
        st.write(f"Le joueur {player_name} a {percentage:.2f}% de matchs avec tie-break.")

# Pour exécuter sur Streamlit, appeler tiebreak_dashboard(saison, db_type="atp" ou "wta")