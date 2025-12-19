import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from typing import List, Dict, Tuple, Optional
from tennis_api import TennisAPI, format_live_matches, RAPIDAPI_KEY
from datetime import datetime, timedelta

@st.cache_data
def load_player_data(file_path: str, player_names: List[str], season: int) -> pd.DataFrame:
    """Charge les données pour plusieurs joueurs"""
    try:
        connexion = sqlite3.connect(file_path)
        placeholders = ",".join(["?"] * len(player_names))
        query = f"""
        SELECT * FROM data 
        WHERE (Winner IN ({placeholders}) OR Loser IN ({placeholders}))
        """
        data = pd.read_sql_query(query, connexion, params=player_names + player_names)
        connexion.close()
        
        # Ajouter une colonne pour le résultat (gagnant/perdant) pour chaque joueur
        results = []
        for player in player_names:
            player_data = data[(data['Winner'] == player) | (data['Loser'] == player)].copy()
            player_data['Result'] = player_data['Winner'].apply(lambda x: 'Victoire' if x == player else 'Défaite')
            player_data['Player'] = player
            results.append(player_data)
            
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return pd.DataFrame()

def get_player_list(file_path: str) -> List[str]:
    """Récupère la liste distincte des joueurs présents dans la base pour alimenter la complétion"""
    try:
        connexion = sqlite3.connect(file_path)
        query = """
        SELECT DISTINCT Winner AS name FROM data
        UNION
        SELECT DISTINCT Loser AS name FROM data
        """
        df_players = pd.read_sql_query(query, connexion)
        connexion.close()

        if "name" in df_players.columns:
            players = (
                df_players["name"]
                .dropna()
                .astype(str)
                .str.strip()
                .sort_values()
                .tolist()
            )
            return players
        return []
    except Exception as e:
        st.error(f"Erreur lors du chargement de la liste des joueurs: {e}")
        return []

def get_player_image_url(player_name: str, circuit: str) -> Optional[str]:
    """Tente de récupérer une URL de photo pour un joueur via l'API externe"""
    try:
        # Si la clé API est la valeur par défaut, on n'essaie pas d'appeler l'API
        if not RAPIDAPI_KEY or RAPIDAPI_KEY == "votre_cle_api_rapidapi":
            return None

        api = TennisAPI()
        results = api.search_players(player_name)

        if results.empty:
            return None

        # Si la colonne name existe, essayer d'abord une correspondance exacte
        row = None
        if "name" in results.columns:
            exact = results[results["name"] == player_name]
            if not exact.empty:
                row = exact.iloc[0]
            else:
                row = results.iloc[0]
        else:
            row = results.iloc[0]

        # Chercher un champ potentiellement utilisable comme URL d'image
        possible_cols = ["image", "profile_image", "picture", "photo"]
        for col in possible_cols:
            if col in results.columns:
                value = row.get(col)
                if isinstance(value, str) and value.startswith("http"):
                    return value

        return None
    except Exception:
        # On ne bloque pas le dashboard si l'API image échoue
        return None

def create_comparison_metrics(data: pd.DataFrame, players: List[str]) -> None:
    """Affiche les métriques comparatives pour les joueurs sélectionnés"""
    st.subheader("Métriques Comparatives")
    
    metrics = []
    for player in players:
        player_data = data[data['Player'] == player]
        wins = len(player_data[player_data['Result'] == 'Victoire'])
        losses = len(player_data[player_data['Result'] == 'Défaite'])
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        metrics.append({
            'Joueur': player,
            'Matchs': total,
            'Victoires': wins,
            'Défaites': losses,
            '% Victoires': f"{win_rate:.1f}%",
            'Titres': len(player_data[(player_data['Round'] == 'The Final') & (player_data['Result'] == 'Victoire')])
        })
    
    st.dataframe(pd.DataFrame(metrics).set_index('Joueur'), use_container_width=True)

def plot_surface_comparison(data: pd.DataFrame, players: List[str]) -> None:
    """Affiche un graphique comparatif des performances par surface"""
    st.subheader("Performances par Surface")
    
    surface_data = []
    for player in players:
        player_data = data[data['Player'] == player]
        for surface in player_data['Surface'].unique():
            surface_matches = player_data[player_data['Surface'] == surface]
            wins = len(surface_matches[surface_matches['Result'] == 'Victoire'])
            total = len(surface_matches)
            if total > 0:
                surface_data.append({
                    'Joueur': player,
                    'Surface': surface,
                    'Taux de victoires': (wins / total) * 100,
                    'Matchs': total
                })
    
    if surface_data:
        df_surface = pd.DataFrame(surface_data)
        fig = px.bar(
            df_surface, 
            x='Surface', 
            y='Taux de victoires',
            color='Joueur',
            barmode='group',
            hover_data=['Matchs'],
            title='Taux de victoires par surface',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        st.plotly_chart(fig, use_container_width=True)

def plot_radar_comparison(data: pd.DataFrame, players: List[str]) -> None:
    """Affiche un radar chart pour comparer plusieurs indicateurs synthétiques entre les joueurs"""
    if len(players) < 2:
        return

    st.subheader("Comparaison synthétique (Radar)")

    metrics = []
    for player in players:
        player_data = data[data["Player"] == player]
        if player_data.empty:
            continue

        wins = (player_data["Result"] == "Victoire").sum()
        total = len(player_data)
        win_rate = (wins / total * 100) if total > 0 else 0

        # Taux de victoires par surface principale
        surfaces = ["Hard", "Clay", "Grass"]
        surface_win_rates = {}
        for s in surfaces:
            sd = player_data[player_data["Surface"] == s]
            if not sd.empty:
                s_wins = (sd["Result"] == "Victoire").sum()
                surface_win_rates[s] = (s_wins / len(sd) * 100)
            else:
                surface_win_rates[s] = 0

        titles = len(
            player_data[
                (player_data["Round"] == "The Final")
                & (player_data["Result"] == "Victoire")
            ]
        )

        metrics.append(
            {
                "player": player,
                "global_win_rate": win_rate,
                "hard_win_rate": surface_win_rates["Hard"],
                "clay_win_rate": surface_win_rates["Clay"],
                "grass_win_rate": surface_win_rates["Grass"],
                "titles": titles,
            }
        )

    if not metrics:
        st.info("Données insuffisantes pour le radar chart.")
        return

    # Normaliser le nombre de titres sur une échelle 0-100 pour l'intégrer au radar
    max_titles = max(m["titles"] for m in metrics) or 1

    categories = [
        "% Victoires global",
        "% Victoires Hard",
        "% Victoires Clay",
        "% Victoires Grass",
        "Titres (normalisés)",
    ]

    fig = go.Figure()
    for m in metrics:
        values = [
            m["global_win_rate"],
            m["hard_win_rate"],
            m["clay_win_rate"],
            m["grass_win_rate"],
            (m["titles"] / max_titles) * 100,
        ]
        # Boucler pour fermer le polygone
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=m["player"],
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Indicateurs synthétiques par joueur",
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_surface_category_heatmap(data: pd.DataFrame, players: List[str]) -> None:
    """Affiche une heatmap des résultats par surface x catégorie de tournoi"""
    st.subheader("Résultats par surface et catégorie de tournoi")

    # Détection de la colonne de catégorie de tournoi
    possible_cols = ["Series", "Level", "Category", "Tier"]
    cat_col = next((c for c in possible_cols if c in data.columns), None)

    if cat_col is None:
        st.info("Aucune colonne de catégorie de tournoi trouvée (Series/Level/Category/Tier).")
        return

    df = data.copy()
    df["Victoire"] = (df["Result"] == "Victoire").astype(int)

    grouped = (
        df.groupby(["Surface", cat_col])["Victoire"]
        .mean()
        .reset_index()
        .rename(columns={"Victoire": "WinRate"})
    )

    if grouped.empty:
        st.info("Données insuffisantes pour la heatmap surface x catégorie.")
        return

    fig = px.density_heatmap(
        grouped,
        x="Surface",
        y=cat_col,
        z="WinRate",
        color_continuous_scale="Viridis",
        labels={"WinRate": "Taux de victoires"},
    )
    fig.update_coloraxes(colorbar_title="Taux de victoires")
    st.plotly_chart(fig, use_container_width=True)

def plot_season_stacked_results(data: pd.DataFrame, players: List[str]) -> None:
    """Affiche des barres empilées victoires/défaites par saison"""
    st.subheader("Victoires / Défaites par saison")

    df = data.copy()

    # Déterminer la saison à partir de la colonne Season ou de la Date
    if "Season" in df.columns:
        df["SeasonYear"] = df["Season"]
    else:
        if "Date" not in df.columns:
            st.info("Impossible de déterminer la saison : colonne Date ou Season manquante.")
            return
        try:
            df["Date"] = pd.to_datetime(df["Date"])
            df["SeasonYear"] = df["Date"].dt.year
        except Exception:
            st.info("Impossible de parser les dates pour calculer la saison.")
            return

    df["Victoire"] = (df["Result"] == "Victoire").astype(int)
    df["Défaite"] = (df["Result"] == "Défaite").astype(int)

    grouped = (
        df.groupby(["SeasonYear", "Player"])[["Victoire", "Défaite"]]
        .sum()
        .reset_index()
        .melt(
            id_vars=["SeasonYear", "Player"],
            value_vars=["Victoire", "Défaite"],
            var_name="Résultat",
            value_name="Matchs",
        )
    )

    if grouped.empty:
        st.info("Données insuffisantes pour les barres empilées par saison.")
        return

    fig = px.bar(
        grouped,
        x="SeasonYear",
        y="Matchs",
        color="Résultat",
        facet_col="Player",
        barmode="stack",
        category_orders={"Résultat": ["Victoire", "Défaite"]},
        labels={"SeasonYear": "Saison", "Matchs": "Nombre de matchs"},
    )
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

def plot_tournament_performance(data: pd.DataFrame, players: List[str]) -> None:
    """Affiche les performances par tournoi"""
    st.subheader("Performances par Tournoi")
    
    tournament_data = []
    for player in players:
        player_data = data[data['Player'] == player]
        for tournament in player_data['Tournament'].unique():
            tourney_matches = player_data[player_data['Tournament'] == tournament]
            wins = len(tourney_matches[tourney_matches['Result'] == 'Victoire'])
            total = len(tourney_matches)
            if total > 0:
                tournament_data.append({
                    'Joueur': player,
                    'Tournoi': tournament,
                    'Taux de victoires': (wins / total) * 100,
                    'Matchs': total,
                    'Titres': len(tourney_matches[(tourney_matches['Round'] == 'The Final') & 
                                                 (tourney_matches['Result'] == 'Victoire')])
                })
    
    if tournament_data:
        df_tournament = pd.DataFrame(tournament_data)
        
        # Filtrer pour n'afficher que les tournois avec un minimum de matchs
        min_matches = st.slider("Nombre minimum de matchs par tournoi", 1, 20, 3)
        df_filtered = df_tournament[df_tournament['Matchs'] >= min_matches]
        
        if not df_filtered.empty:
            fig = px.scatter(
                df_filtered,
                x='Tournoi',
                y='Taux de victoires',
                size='Matchs',
                color='Joueur',
                hover_data=['Titres'],
                title='Performances par tournoi (taille = nombre de matchs)',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig, use_container_width=True)

def display_live_matches():
    """Affiche les matchs en direct"""
    st.subheader("🎾 Matchs en Direct")
    
    api = TennisAPI()
    live_matches = api.get_live_matches()
    
    if not live_matches:
        st.info("Aucun match en cours pour le moment.")
        return
    
    df_matches = format_live_matches(live_matches)
    
    # Afficher chaque match avec des cartes stylisées
    for _, match in df_matches.iterrows():
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.markdown(f"### {match['Joueur 1']}")
            st.markdown(f"**{match['Score 1']}**")
        
        with col2:
            st.markdown("### vs")
            st.markdown("-")
        
        with col3:
            st.markdown(f"### {match['Joueur 2']}")
            st.markdown(f"**{match['Score 2']}**")
        
        # Informations supplémentaires
        st.caption(f"**{match['Tournoi']}** - {match['Tour']} - {match['Statut']}")
        st.markdown("---")

def display_rankings():
    """Affiche les classements ATP/WTA"""
    st.subheader("🏆 Classements")
    
    api = TennisAPI()
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Classement ATP")
        atp_ranking = api.get_ranking('atp', 10)
        if not atp_ranking.empty:
            st.dataframe(
                atp_ranking[['rank', 'name', 'points']]
                .rename(columns={'rank': 'Rang', 'name': 'Joueur', 'points': 'Points'}),
                use_container_width=True
            )
    
    with col2:
        st.markdown("### Classement WTA")
        wta_ranking = api.get_ranking('wta', 10)
        if not wta_ranking.empty:
            st.dataframe(
                wta_ranking[['rank', 'name', 'points']]
                .rename(columns={'rank': 'Rang', 'name': 'Joueuse', 'points': 'Points'}),
                use_container_width=True
            )

def advanced_dashboard():
    """Affiche le tableau de bord avancé"""
    st.title("🎾 Tableau de Bord Tennis en Temps Réel")
    
    # Onglets pour naviguer entre les différentes vues
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparaison des Joueurs", "🎾 Matchs en Direct", "🏆 Classements", "📅 Prochains Tournois"])
    
    with tab1:
        st.title("🔍 Comparaison des Joueurs")
    
    with st.sidebar:
        st.header("Paramètres de comparaison")
        # Sélection de la saison
        season = st.number_input("Sélectionnez la saison", min_value=2000, max_value=2100, value=2024)
        
        # Sélection du circuit (ATP/WTA)
        circuit = st.radio("Circuit", ["ATP", "WTA"])
        
        # Bouton pour actualiser les données en temps réel
        use_realtime = st.checkbox("Afficher les données en temps réel (nécessite une connexion Internet)")
    
    file_path = f"Data_Base_Tennis/{circuit.lower()}_{season}.db"
    
    # Sélection des deux joueurs à comparer avec complétion
    st.sidebar.subheader("Sélection des joueurs")
    available_players = get_player_list(file_path)

    if not available_players:
        st.warning("Impossible de récupérer la liste des joueurs pour cette saison/circuit.")
        return

    player1 = st.sidebar.selectbox(
        "Joueur 1",
        options=available_players,
        index=0 if available_players else None,
    )

    # Filtrer la liste pour le second joueur afin d'éviter de choisir deux fois le même
    remaining_players = [p for p in available_players if p != player1]

    player2 = st.sidebar.selectbox(
        "Joueur 2",
        options=remaining_players if remaining_players else available_players,
        index=0 if (remaining_players or available_players) else None,
    )

    player_names = [p for p in [player1, player2] if p]
    
    if not player_names:
        st.warning("Veuillez entrer au moins un nom de joueur")
        return
    
    # Chargement des données
    data = load_player_data(file_path, player_names, season)
    
    if data.empty:
        st.warning("Aucune donnée trouvée pour les joueurs sélectionnés")
        return
    
    # Affichage des onglets
    tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "🎾 Par Surface", "🏆 Par Tournoi"])
    
    with tab1:
        # Affichage des photos des joueurs (si disponibles)
        photo_cols = st.columns(len(player_names)) if player_names else []
        for col, player in zip(photo_cols, player_names):
            with col:
                img_url = get_player_image_url(player, circuit.lower())
                if img_url:
                    st.image(img_url, width=120, caption=player)
                else:
                    st.markdown(f"**{player}**")

        create_comparison_metrics(data, player_names)
        
        # Graphique d'évolution dans le temps
        st.subheader("Évolution des performances dans le temps")
        try:
            data['Date'] = pd.to_datetime(data['Date'])
            data_sorted = data.sort_values('Date')
            
            # Calcul du taux de victoires glissant
            rolling_wins = []
            for player in player_names:
                player_data = data_sorted[data_sorted['Player'] == player].copy()
                player_data['Cumulative Wins'] = (player_data['Result'] == 'Victoire').cumsum()
                player_data['Cumulative Matches'] = range(1, len(player_data) + 1)
                player_data['Win Rate'] = (player_data['Cumulative Wins'] / player_data['Cumulative Matches']) * 100
                rolling_wins.append(player_data)
            
            df_rolling = pd.concat(rolling_wins)
            
            fig = px.line(
                df_rolling, 
                x='Date', 
                y='Win Rate',
                color='Player',
                title='Taux de victoires cumulé (fenêtre glissante)',
                markers=True,
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_layout(yaxis_title='Taux de victoires (%)')
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Impossible d'afficher l'évolution dans le temps : {e}")
        
        # Radar chart de comparaison synthétique
        plot_radar_comparison(data, player_names)
        
        # Heatmap surface x catégorie de tournoi
        plot_surface_category_heatmap(data, player_names)
        
        # Barres empilées victoires/défaites par saison
        plot_season_stacked_results(data, player_names)
    
    with tab2:
        display_live_matches()
        
    with tab3:
        display_rankings()
        
        # Ajouter des graphiques supplémentaires pour les classements
        st.subheader("Évolution du Top 10")
        st.info("Fonctionnalité d'évolution du classement à venir dans une prochaine mise à jour.")
        
    with tab4:
        st.subheader("Prochains Tournois")
        api = TennisAPI()
        today = datetime.now()
        next_month = today + timedelta(days=30)
        tournaments = api.get_tournaments(today.strftime('%Y-%m-%d'), next_month.strftime('%Y-%m-%d'))
        
        if not tournaments.empty:
            # Filtrer et formater les données
            tournaments = tournaments[['name', 'startDate', 'endDate', 'category', 'surface']]
            tournaments['startDate'] = pd.to_datetime(tournaments['startDate']).dt.strftime('%d/%m/%Y')
            tournaments['endDate'] = pd.to_datetime(tournaments['endDate']).dt.strftime('%d/%m/%Y')
            
            # Afficher les tournois à venir
            st.dataframe(
                tournaments.rename(columns={
                    'name': 'Tournoi',
                    'startDate': 'Début',
                    'endDate': 'Fin',
                    'category': 'Catégorie',
                    'surface': 'Surface'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Aucun tournoi à venir dans le mois prochain.")
    
    # Onglet de comparaison des joueurs (tab1)
    with tab1:
        plot_surface_comparison(data, player_names)
        
        # Détails des matchs par surface
        st.subheader("Détails des matchs par surface")
        surface = st.selectbox("Sélectionnez une surface", data['Surface'].unique())
        
        for player in player_names:
            player_surface_data = data[(data['Player'] == player) & (data['Surface'] == surface)]
            if not player_surface_data.empty:
                wins = len(player_surface_data[player_surface_data['Result'] == 'Victoire'])
                total = len(player_surface_data)
                st.metric(
                    label=f"{player} - {surface}",
                    value=f"{wins}V - {total-wins}D",
                    delta=f"{(wins/total*100):.1f}% de victoires" if total > 0 else "N/A"
                )
    
    with tab3:
        plot_tournament_performance(data, player_names)
        
        # Détails des titres
        st.subheader("Titres remportés")
        for player in player_names:
            titles = data[(data['Player'] == player) & 
                         (data['Round'] == 'The Final') & 
                         (data['Result'] == 'Victoire')]
            if not titles.empty:
                st.write(f"**{player}** a remporté {len(titles)} titres en {season}:")
                st.dataframe(
                    titles[['Tournament', 'Surface', 'Loser']]
                          .rename(columns={'Tournament': 'Tournoi', 'Loser': 'Finaliste battu'})
                          .reset_index(drop=True),
                    use_container_width=True
                )

if __name__ == "__main__":
    advanced_dashboard()
