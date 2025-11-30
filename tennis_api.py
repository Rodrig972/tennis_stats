import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple

# Configuration de l'API (à remplacer par votre clé API)
# Inscrivez-vous sur https://rapidapi.com/tipsters/api/tennisapi1/ pour obtenir une clé
RAPIDAPI_KEY = os.getenv('TENNIS_API_KEY', 'votre_cle_api_rapidapi')
RAPIDAPI_HOST = "tennisapi1.p.rapidapi.com"

class TennisAPI:
    """Classe pour interagir avec l'API de données de tennis"""
    
    def __init__(self):
        self.headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        self.base_url = f"https://{RAPIDAPI_HOST}"
    
    def get_ranking(self, ranking_type: str = 'atp', limit: int = 100) -> pd.DataFrame:
        """Récupère le classement ATP/WTA"""
        url = f"{self.base_url}/api/tennis/rankings/{ranking_type}"
        querystring = {"limit": str(limit)}
        
        try:
            response = requests.get(url, headers=self.headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            
            if 'rankings' in data:
                return pd.DataFrame(data['rankings'])
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération du classement: {e}")
            return pd.DataFrame()
    
    def get_player_stats(self, player_id: str) -> Dict:
        """Récupère les statistiques détaillées d'un joueur"""
        url = f"{self.base_url}/api/tennis/player/{player_id}/stats"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Erreur lors de la récupération des statistiques du joueur: {e}")
            return {}
    
    def get_live_matches(self) -> List[Dict]:
        """Récupère les matchs en cours"""
        url = f"{self.base_url}/api/tennis/event/live"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('events', [])
        except Exception as e:
            st.error(f"Erreur lors de la récupération des matchs en direct: {e}")
            return []
    
    def get_tournaments(self, date_from: str = None, date_to: str = None) -> pd.DataFrame:
        """Récupère la liste des tournois"""
        url = f"{self.base_url}/api/tennis/tournaments"
        
        # Définir la plage de dates par défaut (mois en cours)
        if not date_from:
            date_from = datetime.now().strftime('%Y-%m-01')
        if not date_to:
            next_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)
            date_to = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
        
        querystring = {
            "from": date_from,
            "to": date_to
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            
            if 'tournaments' in data:
                return pd.DataFrame(data['tournaments'])
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des tournois: {e}")
            return pd.DataFrame()
    
    def search_players(self, query: str) -> pd.DataFrame:
        """Recherche des joueurs par nom"""
        url = f"{self.base_url}/api/tennis/search/players"
        querystring = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            
            if 'players' in data:
                return pd.DataFrame(data['players'])
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erreur lors de la recherche de joueurs: {e}")
            return pd.DataFrame()

# Fonction utilitaire pour formater les données des matchs en direct
def format_live_matches(matches: List[Dict]) -> pd.DataFrame:
    """Formate les données des matchs en direct pour l'affichage"""
    formatted_matches = []
    
    for match in matches:
        home_team = match.get('homeTeam', {}).get('name', 'Inconnu')
        away_team = match.get('awayTeam', {}).get('name', 'Inconnu')
        tournament = match.get('tournament', {}).get('name', 'Tournoi inconnu')
        round_info = match.get('roundInfo', {})
        
        score = match.get('score', {})
        home_score = score.get('home', 0)
        away_score = score.get('away', 0)
        
        formatted_matches.append({
            'Joueur 1': home_team,
            'Score 1': home_score,
            'Joueur 2': away_team,
            'Score 2': away_score,
            'Tournoi': tournament,
            'Tour': round_info.get('name', 'N/A'),
            'Statut': match.get('status', {}).get('description', 'En cours')
        })
    
    return pd.DataFrame(formatted_matches)

# Exemple d'utilisation
if __name__ == "__main__":
    api = TennisAPI()
    
    # Exemple: Récupérer le classement ATP
    ranking = api.get_ranking('atp', 10)
    if not ranking.empty:
        print("Top 10 ATP:")
        print(ranking[['rank', 'name', 'points']])
    
    # Exemple: Récupérer les matchs en direct
    live_matches = api.get_live_matches()
    if live_matches:
        print("\nMatchs en direct:")
        for match in live_matches:
            home = match.get('homeTeam', {}).get('name', 'Inconnu')
            away = match.get('awayTeam', {}).get('name', 'Inconnu')
            score = match.get('score', {})
            print(f"{home} {score.get('home', 0)} - {score.get('away', 0)} {away}")
