import pandas as pd
import sqlite3

# Fonction pour convertir un fichier .xlsx en .db
def excel_to_db(excel_file, db_file):
    # Lire le fichier Excel
    df = pd.read_excel(excel_file)

    # Créer une connexion à la base de données SQLite
    conn = sqlite3.connect(db_file)

    # Écrire le DataFrame dans la base de données
    df.to_sql('data', conn, if_exists='replace', index=False)

    # Fermer la connexion
    conn.close()
    print(f'Le fichier {excel_file} a été converti en {db_file}.')

# Exemple d'utilisation
if __name__ == "__main__":
    excel_file = './Data_Base_Tennis/atp_2025.xlsx'  # Remplacez par le chemin de votre fichier .xlsx
    db_file = './Data_Base_Tennis/atp_2025.db'        # Remplacez par le nom de votre fichier .db
    excel_to_db(excel_file, db_file)
