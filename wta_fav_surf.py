import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def get_wta_favorites_by_surface(season):
    file_path = f"Data_Base_Tennis/wta_{season}.db"
    try:
        conn = sqlite3.connect(file_path)
        query = """
        SELECT Surface, Winner, COUNT(*) AS Victoires
        FROM data
        GROUP BY Surface, Winner
        ORDER BY Surface, Victoires DESC;
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        return data
    except sqlite3.Error:
        st.error(f"Base de données WTA {season} introuvable.")
        return pd.DataFrame()

def wta_fav_surface_dashboard(season):
    st.title(f"Favoris par surface - WTA {season}")
    data = get_wta_favorites_by_surface(season)
    if data.empty:
        st.warning("Aucune donnée trouvée.")
    else:
        for surface in data["Surface"].unique():
            st.header(f"Top 10 joueuses - {surface}")
            surface_data = data[data["Surface"] == surface].head(10)
            st.dataframe(surface_data)
