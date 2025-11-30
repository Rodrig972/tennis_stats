import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from typing import List, Dict, Tuple, Optional
from tennis_api import TennisAPI, format_live_matches
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
    
    # Saisie des joueurs à comparer
    st.sidebar.subheader("Sélection des joueurs")
    player_input = st.sidebar.text_area(
        "Entrez les noms des joueurs (un par ligne)",
        "Djokovic N.\nNadal R.\nFederer R.",
        help="Format: 'Nom Prénom' ou 'Nom P.' (ex: 'Djokovic N.')"
    )
    
    # Si l'utilisateur a coché l'option de données en temps réel
    if use_realtime:
        st.sidebar.info("🔍 La recherche de joueurs en temps réel est activée.")
        search_query = st.sidebar.text_input("Rechercher un joueur (temps réel)", "")
        
        if search_query and len(search_query) > 2:  # Ne pas chercher pour moins de 3 caractères
            api = TennisAPI()
            search_results = api.search_players(search_query)
            
            if not search_results.empty:
                st.sidebar.write("Résultats de la recherche:")
                for _, player in search_results.iterrows():
                    if st.sidebar.button(f"Ajouter {player.get('name', 'Inconnu')}"):
                        player_input = f"{player_input}\n{player.get('name', '')}"
                        st.experimental_rerun()
    player_names = [name.strip() for name in player_input.split('\n') if name.strip()]
    
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
