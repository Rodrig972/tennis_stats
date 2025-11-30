import sqlite3
import pandas as pd
import sweetviz as sv

# Chemin de la base de données
db_path = "Data_Base_Tennis/atp_2024.db"


# Connexion à la base de données
conn = sqlite3.connect(db_path)

# Lire les données depuis la table souhaitée (remplace 'nom_de_ta_table' par le nom réel de ta table)
table_name = "data"  #Nom de la table
df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

# Générer un rapport Sweetviz
report = sv.analyze(df)
report.show_html("rapport_sweetviz.html")  # Génère un fichier HTML

print("Le rapport Sweetviz a été généré : rapport_sweetviz.html")
