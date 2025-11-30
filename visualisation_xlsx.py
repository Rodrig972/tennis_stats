import pandas as pd
import sweetviz as sv

# Charger le fichier Excel
file_path = "Data_Base_Tennis/Tennis_Pronos.xlsx"
df = pd.read_excel(file_path)

# Générer un rapport Sweetviz
report = sv.analyze(df)
report.show_html("rapport_sweetviz.html")  # Génère un fichier HTML

print("Le rapport Sweetviz a été généré : rapport_sweetviz.html")