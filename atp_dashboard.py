import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

@st.cache_data
def load_data(file_path, player_name, surface_condition="", series_condition=""):
    try:
        connexion = sqlite3.connect(file_path)
        query = f"""
        SELECT Series, Tournament, Surface, Round, Winner, Loser, W1, L1, W2, L2, W3, L3, W4, L4, W5, L5, Wsets, Lsets
        FROM data
        WHERE (Winner = ? OR Loser = ?) {surface_condition} {series_condition};
        """
        data = pd.read_sql_query(query, connexion, params=(player_name, player_name))
        connexion.close()
        return data
    except (sqlite3.OperationalError, pd.errors.DatabaseError):
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur

def load_three_set_matches(file_path, player_name):
    try:
        connexion = sqlite3.connect(file_path)
        query = """
        SELECT Series, Tournament, Date, Round, Winner, Loser, Surface
        FROM data
        WHERE (Series <> 'Grand Slam' and (Lsets = 1.0 and Wsets = 2.0) and (Winner = ? or Loser = ?));
        """
        data = pd.read_sql_query(query, connexion, params=(player_name, player_name))
        connexion.close()
        return data
    except (sqlite3.OperationalError, pd.errors.DatabaseError):
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur

def calculate_statistics(data, player_name):
    stats = {
        "Nombre de matchs": len(data),
        "Nombre de victoires": len(data[data["Winner"] == player_name]),
        "Nombre de défaites": len(data[data["Loser"] == player_name]),
        "Titres remportés": len(data[(data["Winner"] == player_name) & (data["Round"] == "The Final")]),
        "Titres en Grand Slam": len(data[(data["Winner"] == player_name) & (data["Round"] == "The Final") & (data["Series"] == "Grand Slam")]),
    }

    surface_titles = data[(data["Winner"] == player_name) & (data["Round"] == "The Final")].groupby("Surface").size().reset_index(name="Titres")
    stats["Titres par surface"] = surface_titles

    tournaments_won = data[(data["Winner"] == player_name) & (data["Round"] == "The Final")][["Tournament", "Series"]]
    stats["Tournois remportés"] = tournaments_won

    # Calcul du nombre de matchs en 3 sets par surface
    three_set_matches = data[(data["Wsets"] + data["Lsets"] == 3)]
    stats["Matchs en 3 sets par surface"] = three_set_matches.groupby("Surface").size().reset_index(name="Matchs en 3 sets")

    return stats

def calculate_average_sets(data, player_name):
    data["Sets_joués"] = data["Wsets"] + data["Lsets"]

    grand_slam_matches = data[data["Series"] == "Grand Slam"]
    total_sets_grand_slam = grand_slam_matches["Sets_joués"].sum()
    total_matches_grand_slam = len(grand_slam_matches)

    avg_sets_grand_slam = (
        total_sets_grand_slam / total_matches_grand_slam
        if total_matches_grand_slam > 0
        else 0
    )

    non_grand_slam_matches = data[data["Series"] != "Grand Slam"]
    total_sets_non_grand_slam = non_grand_slam_matches["Sets_joués"].sum()
    total_matches_non_grand_slam = len(non_grand_slam_matches)

    avg_sets_non_grand_slam = (
        total_sets_non_grand_slam / total_matches_non_grand_slam
        if total_matches_non_grand_slam > 0
        else 0
    )

    return avg_sets_grand_slam, avg_sets_non_grand_slam

def atp_dashboard(player_name, season, surface_condition="", series_condition=""):
    file_path = f"Data_Base_Tennis/atp_{season}.db"

    data = load_data(file_path, player_name, surface_condition, series_condition)
    three_set_matches = load_three_set_matches(file_path, player_name)

    if data.empty:
        st.warning("Aucune donnée trouvée pour ce joueur avec les filtres sélectionnés.")
        return

    stats = calculate_statistics(data, player_name)
    avg_sets_grand_slam, avg_sets_non_grand_slam = calculate_average_sets(data, player_name)

    st.header(f"Statistiques générales - {season} - {player_name}")
    col1, col2 = st.columns(2)
    col1.metric("Nombre de matchs", stats["Nombre de matchs"])
    col1.metric("Nombre de victoires", stats["Nombre de victoires"])
    col2.metric("Nombre de défaites", stats["Nombre de défaites"])
    col2.metric("Titres remportés", stats["Titres remportés"])
    col2.metric("Titres en Grand Slam", stats["Titres en Grand Slam"])

    st.metric("Moyenne de sets/match (hors Grand Slam)", f"{avg_sets_non_grand_slam:.2f}")
    st.metric("Moyenne de sets/match (Grand Slam)", f"{avg_sets_grand_slam:.2f}")

    st.header("Titres remportés par surface")
    if not stats["Titres par surface"].empty:
        st.dataframe(stats["Titres par surface"])
        fig = px.bar(stats["Titres par surface"], x="Surface", y="Titres", title="Titres remportés par surface", text="Titres")
        st.plotly_chart(fig)
    else:
        st.write("Aucun titre remporté pour les surfaces sélectionnées.")

    st.header("Performances par surface")
    surface_stats = data.groupby("Surface").agg(
        Victoires=("Winner", lambda x: (x == player_name).sum()),
        Défaites=("Loser", lambda x: (x == player_name).sum()),
    ).reset_index()
    surface_stats["Total"] = surface_stats["Victoires"] + surface_stats["Défaites"]

    fig = px.bar(
        surface_stats,
        x="Surface",
        y=["Victoires", "Défaites"],
        title="Performances par surface",
        barmode="group",
        text_auto=True,
    )
    st.plotly_chart(fig)

    st.header("Matchs en 3 sets")
    if not three_set_matches.empty:
        st.dataframe(three_set_matches)
        # Calcul de la moyenne des matchs en 3 sets
        total_matches = stats["Nombre de matchs"]
        total_three_set_matches = len(three_set_matches)
        avg_three_set_matches = (total_three_set_matches / total_matches) * 100 if total_matches > 0 else 0
        st.metric("Pourcentage de matchs en 3 sets", f"{avg_three_set_matches:.2f}%")
    else:
        st.write("Aucun match en 3 sets trouvé.")

    st.header("Tournois remportés")
    if not stats["Tournois remportés"].empty:
        st.dataframe(stats["Tournois remportés"])
    else:
        st.write("Aucun tournoi remporté.")

    st.header("Détails des matchs")
    st.dataframe(data)

    tournament_stats = data[data["Winner"] == player_name]["Tournament"].value_counts().reset_index()
    tournament_stats.columns = ["Tournoi", "Victoires"]
    fig2 = px.pie(tournament_stats, names="Tournoi", values="Victoires", title="Répartition des victoires par tournoi")
    st.plotly_chart(fig2)