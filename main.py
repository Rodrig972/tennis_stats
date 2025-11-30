import streamlit as st
from atp_dashboard import atp_dashboard
from wta_dashboard import wta_dashboard
from atp_fav_surf import atp_fav_surface_dashboard
from wta_fav_surf import wta_fav_surface_dashboard
from atp_three_sets import atp_three_set_non_slam_dashboard
from wta_three_sets import wta_three_set_dashboard
from advanced_dashboard import advanced_dashboard

# Import des nouvelles fonctionnalités
from atp_tiebreaks import tiebreak_dashboard as atp_tiebreak_dashboard
from wta_tiebreaks import tiebreak_dashboard as wta_tiebreak_dashboard

st.set_page_config(page_title="Tableau de bord Tennis", layout="wide")

st.title("Tableau de bord des performances des joueurs ATP et WTA")

st.sidebar.title("Menu principal")
menu = st.sidebar.radio(
    "Choisissez une option :",
    ["Dashboard ATP", "Dashboard WTA", "Comparaison avancée", "Favoris surface", "Matchs en 3 sets", "Tie-breaks"],
)

if menu == "Dashboard ATP":
    # Saisie de l'année
    season = st.sidebar.number_input("Entrez l'année de la saison (ex : 2024)", min_value=2000, max_value=2100, value=2024)
    player_name = st.sidebar.text_input("Nom du joueur (ex : 'Djokovic N.')")
    if player_name:
        try:
            atp_dashboard(player_name, season)
        except Exception as e:
            st.error(f"Aucune donnée trouvée pour ce joueur avec les filtres sélectionnés. (Erreur : {str(e)})")

elif menu == "Dashboard WTA":
    # Saisie de l'année
    season = st.sidebar.number_input("Entrez l'année de la saison (ex : 2024)", min_value=2000, max_value=2100, value=2024)
    player_name = st.sidebar.text_input("Nom de la joueuse (ex : 'Swiatek I.')")
    if player_name:
        try:
            wta_dashboard(player_name, season)
        except Exception as e:
            st.error(f"Aucune donnée trouvée pour ce joueur avec les filtres sélectionnés. (Erreur : {str(e)})")

elif menu == "Favoris surface":
    fav_menu = st.sidebar.radio("Choisissez une option :", ["ATP", "WTA"])
    season = st.sidebar.number_input("Entrez l'année de la saison (ex : 2024)", min_value=2000, max_value=2100, value=2024)

    try:
        if fav_menu == "ATP":
            atp_fav_surface_dashboard(season)
        elif fav_menu == "WTA":
            wta_fav_surface_dashboard(season)
    except Exception as e:
        st.error(f"Aucune donnée trouvée pour cette année. (Erreur : {str(e)})")

elif menu == "Matchs en 3 sets":
    set_menu = st.sidebar.radio("Choisissez une option :", ["ATP", "WTA"])
    season = st.sidebar.number_input("Entrez l'année de la saison (ex : 2024)", min_value=2000, max_value=2100, value=2024)

    try:
        if set_menu == "ATP":
            atp_three_set_non_slam_dashboard(season)
        elif set_menu == "WTA":
            wta_three_set_dashboard(season)
    except Exception as e:
        st.error(f"Aucune donnée trouvée pour cette année. (Erreur : {str(e)})")

elif menu == "Comparaison avancée":
    advanced_dashboard()
    
elif menu == "Tie-breaks":
    tiebreak_menu = st.sidebar.radio("Choisissez une option :", ["ATP", "WTA"])
    season = st.sidebar.number_input("Entrez l'année de la saison (ex : 2024)", min_value=2000, max_value=2100, value=2024)

    try:
        if tiebreak_menu == "ATP":
            atp_tiebreak_dashboard(season)
        elif tiebreak_menu == "WTA":
            wta_tiebreak_dashboard(season)
    except Exception as e:
        st.error(f"Aucune donnée trouvée pour cette année. (Erreur : {str(e)})")