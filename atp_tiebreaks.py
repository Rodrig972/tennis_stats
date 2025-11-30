import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def get_top_tiebreak_players(season):
    """
    Récupère le top 15 des joueurs avec le plus de matchs avec tie-break hors Grand Chelem.
    """
    file_path = f"Data_Base_Tennis/atp_{season}.db"
    try:
        conn = sqlite3.connect(file_path)
        query = """
        SELECT Series, Tournament, Surface, Date, Round, Winner, Loser, L1, W1, L2, W2, L3, W3
        FROM data 
        WHERE Series <> 'Grand Slam' AND 
              (L1 + W1 = 13 OR L2 + W2 = 13 OR L3 + W3 = 13);
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Compter le nombre de fois où chaque joueur apparaît dans Winner ou Loser
        players = pd.concat([df["Winner"], df["Loser"]])
        top_players = players.value_counts().head(15).reset_index()
        top_players.columns = ["Joueur", "Nombre de matchs avec tie-break"]
        
        return top_players, df
    except sqlite3.Error:
        st.error(f"Base de données ATP {season} introuvable.")
        return pd.DataFrame(), pd.DataFrame()

def get_player_matches(player_name, season):
    """
    Récupère tous les matchs d'un joueur spécifique (hors Grand Chelem).
    """
    file_path = f"Data_Base_Tennis/atp_{season}.db"
    try:
        conn = sqlite3.connect(file_path)
        query = f"""
        SELECT Series, Tournament, Surface, Date, Round, Winner, Loser, L1, W1, L2, W2, L3, W3
        FROM data
        WHERE Series <> 'Grand Slam' AND (Winner = '{player_name}' OR Loser = '{player_name}');
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except sqlite3.Error:
        st.error(f"Base de données ATP {season} introuvable.")
        return pd.DataFrame()

def get_player_tiebreak_percentage(player_name, season):
    """
    Calcule le pourcentage de matchs avec tie-break pour un joueur spécifique.
    """
    # Récupérer tous les matchs du joueur (hors Grand Chelem)
    player_matches = get_player_matches(player_name, season)
    if player_matches.empty:
        return 0
    
    # Compter les matchs avec au moins un tie-break
    tiebreak_matches = player_matches[
        ((player_matches["W1"] == 7.0) & (player_matches["L1"] == 6.0)) |
        ((player_matches["W1"] == 6.0) & (player_matches["L1"] == 7.0)) |
        ((player_matches["W2"] == 7.0) & (player_matches["L2"] == 6.0)) |
        ((player_matches["W2"] == 6.0) & (player_matches["L2"] == 7.0)) |
        ((player_matches["W3"] == 7.0) & (player_matches["L3"] == 6.0)) |
        ((player_matches["W3"] == 6.0) & (player_matches["L3"] == 7.0))
    ]
    
    # Calculer le pourcentage
    total_matches = len(player_matches)
    if total_matches > 0:
        percentage = (len(tiebreak_matches) / total_matches) * 100
        return percentage
    else:
        return 0

def tiebreak_dashboard(season):
    """
    Affiche le tableau de bord des tie-breaks pour l'ATP.
    """
    st.title(f"Top 15 des joueurs avec le plus de matchs avec tie-break (hors Grand Chelem) - ATP {season}")
    
    # Récupérer le top 15 des joueurs avec tie-breaks
    top_players, df = get_top_tiebreak_players(season)
    if top_players.empty:
        st.warning("Aucune donnée trouvée.")
    else:
        st.dataframe(top_players)
    
    # Recherche d'un joueur spécifique
    st.title("Pourcentage de matchs avec tie-break pour un joueur")
    player_name = st.text_input("Entrez le nom du joueur (ex : 'Machac T.'):")
    
    if player_name:
        percentage = get_player_tiebreak_percentage(player_name, season)
        st.write(f"Le joueur {player_name} a {percentage:.2f}% de matchs avec tie-break (hors Grand Chelem).")