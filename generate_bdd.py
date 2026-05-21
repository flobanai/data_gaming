import pandas as pd
import os

# ==========================================================
# 1. LECTURE DES FICHIERS SOURCES
# ==========================================================
file_action = "action.csv"
file_sante = "Gaming and Mental Health.csv"
file_jeux = "Video_games_esrb_rating.csv"

print("Lecture des fichiers sources...")
# On laisse Pandas lire toutes les colonnes (on enlève index_col=0)
df_films = pd.read_csv(file_action, sep=None, engine='python')
df_sante = pd.read_csv(file_sante, sep=None, engine='python')
df_jeux = pd.read_csv(file_jeux, sep=None, engine='python')

# NETTOYAGE : On enlève les espaces inutiles et on supprime les colonnes d'index parasites (Unnamed: 0 ou 0)
for df in [df_films, df_sante, df_jeux]:
    df.columns = df.columns.str.strip()
    cols_to_drop = ['Unnamed: 0', '0']
    df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True, errors='ignore')

print("Colonnes lues dans action.csv :", df_films.columns.tolist())
print("Colonnes lues dans Gaming and Mental Health.csv :", df_sante.columns.tolist())
print("Colonnes lues dans Video_games_esrb_rating.csv :", df_jeux.columns.tolist())

# ==========================================================
# 2. CRÉATION DE LA TABLE GENRE
# ==========================================================
print("\nCréation de la table GENRE...")
genres_films = df_films['genre'].str.split(',', expand=True).stack().str.strip().unique()
genres_jeux = df_sante['game_genre'].str.strip().unique()

tous_les_genres = list(set(list(genres_films) + list(genres_jeux)))

violence_mapping = {
    'FPS': 5, 'Shooter': 5, 'Battle Royale': 5, 'MOBA': 4, 'Action': 4, 'Thriller': 4, 'Crime': 4, 'War': 5,
    'Horreur': 5, 'Horror': 5, 'RPG': 3, 'Sci-Fi': 3, 'Fantasy': 3, 'Adventure': 2, 'Strategy': 2,
    'Drama': 2, 'Mystery': 2, 'Animation': 1, 'Comedy': 1, 'Romance': 1, 'Mobile Games': 1, 'Simulation': 1, 'MMO': 3
}

df_genre = pd.DataFrame(tous_les_genres, columns=['nom_genre'])
df_genre['niveau_violence_estime'] = df_genre['nom_genre'].map(violence_mapping).fillna(2).astype(int)
df_genre.insert(0, 'id_genre', range(1, len(df_genre) + 1))

# ==========================================================
# 3. CRÉATION DE LA TABLE INDIVIDU
# ==========================================================
print("Création de la table INDIVIDU...")
# On génère nous-mêmes un ID propre 1, 2, 3... qu'on met aussi dans df_sante pour la liaison plus tard
df_sante['id_individu'] = range(1, len(df_sante) + 1)

df_individu = pd.DataFrame()
df_individu['id_individu'] = df_sante['id_individu']
df_individu['pseudo'] = "Joueur" + df_individu['id_individu'].astype(str)
df_individu['age'] = df_sante['age']
df_individu['sexe'] = df_sante['gender'].map({'Male': 'Homme', 'Female': 'Femme', 'Other': 'Non-binaire'})

mood_score = {'Normal': 8, 'Excited': 9, 'Euphoric': 7, 'Restless': 5, 'Anxious': 4, 'Irritable': 3, 'Angry': 2, 'Depressed': 1, 'Withdrawn': 2}
df_individu['score_sante_mentale'] = df_sante['mood_state'].map(mood_score).fillna(5)
df_individu['score_sante_mentale'] = (df_individu['score_sante_mentale'] - (df_sante['social_isolation_score'] * 0.3)).clip(0, 10).round(0).astype(int)

sleep_score = {'Good': 8, 'Fair': 6, 'Poor': 4, 'Very Poor': 2, 'Insomnia': 1}
df_individu['score_qualite_sommeil'] = df_sante['sleep_quality'].map(sleep_score).fillna(5)

df_individu['score_sante_physique'] = 10 - (df_sante[['eye_strain', 'back_neck_pain']].sum(axis=1) * 1.5) + (df_sante['exercise_hours_weekly'] * 0.2)
df_individu['score_sante_physique'] = df_individu['score_sante_physique'].clip(0, 10).round(0).astype(int)

# ==========================================================
# 4. CRÉATION DE LA TABLE MEDIA
# ==========================================================
print("Création de la table MEDIA...")
df_media_jeux = pd.DataFrame()
df_media_jeux['titre'] = df_jeux['titre'].str.strip()
df_media_jeux['type_media'] = 'Jeu Video'
df_media_jeux['classification_age'] = df_jeux['classification_age']
df_media_jeux['est_violent'] = df_jeux['est_violent'].map({True: 1, 'TRUE': 1, False: 0, 'FALSE': 0}).fillna(0).astype(int)

df_media_films = pd.DataFrame()
df_media_films['titre'] = df_films['movie_name'].str.strip()
df_media_films['type_media'] = 'Film'
cert_mapping = {'R': 'Interdit -16', 'PG-13': '12+', 'PG': 'TP', 'Not Rated': 'Non classé', 'TV-MA': '18+'}
df_media_films['classification_age'] = df_films['certificate'].map(cert_mapping).fillna('Non classé')
df_media_films['est_violent'] = df_films['certificate'].isin(['R', 'TV-MA']).astype(int)

df_media = pd.concat([df_media_jeux, df_media_films], ignore_index=True)
df_media = df_media.drop_duplicates(subset=['titre']).reset_index(drop=True)
df_media.insert(0, 'id_media', range(1, len(df_media) + 1))

# ==========================================================
# 5. CRÉATION DE LA TABLE APPARTENIR
# ==========================================================
print("Création de la table APPARTENIR...")
lignes_appartenir = []

for index, row in df_films.iterrows():
    titre = str(row['movie_name']).strip()
    genres = str(row['genre']).split(',')
    for g in genres:
        g_propre = g.strip()
        lignes_appartenir.append({'titre': titre, 'nom_genre': g_propre})

for index, row in df_sante.iterrows():
    titre = str(row['primary_game']).strip()
    g_propre = str(row['game_genre']).strip()
    lignes_appartenir.append({'titre': titre, 'nom_genre': g_propre})

df_appartenir_temp = pd.DataFrame(lignes_appartenir)
df_appartenir_temp = df_appartenir_temp.drop_duplicates()

df_appartenir = df_appartenir_temp.merge(df_media[['id_media', 'titre']], on='titre')
df_appartenir = df_appartenir.merge(df_genre[['id_genre', 'nom_genre']], on='nom_genre')
df_appartenir = df_appartenir[['id_media', 'id_genre']]

# ==========================================================
# 6. CRÉATION DE LA TABLE CONSOMMER
# ==========================================================
print("Création de la table CONSOMMER...")

# On prépare les données de consommation AVANT la jointure
df_sante_temp = df_sante.copy()
df_sante_temp['titre'] = df_sante_temp['primary_game'].str.strip()
df_sante_temp['heures_hebdomadaires'] = (df_sante_temp['daily_gaming_hours'] * 7).round(1)

def get_frequence(hours_per_day):
    if pd.isna(hours_per_day): return 'Occasionnel'
    if hours_per_day >= 4: return 'Quotidien'
    if hours_per_day >= 1.5: return 'Hebdomadaire'
    return 'Occasionnel'

df_sante_temp['frequence'] = df_sante_temp['daily_gaming_hours'].apply(get_frequence)

# On fait la jointure
df_consommer = df_sante_temp.merge(df_media[['id_media', 'titre']], on='titre', how='inner')

# On ne garde que les colonnes finales
df_consommer = df_consommer[['id_individu', 'id_media', 'heures_hebdomadaires', 'frequence']]
df_consommer = df_consommer.drop_duplicates(subset=['id_individu', 'id_media'])

# ==========================================================
# 7. EXPORTATION DES FICHIERS CSV PROPRES
# ==========================================================
print("Exportation des CSV finaux...")
os.makedirs('csv_pour_bdd', exist_ok=True)

df_genre.to_csv('csv_pour_bdd/genre.csv', index=False, sep=',')
df_individu.to_csv('csv_pour_bdd/individu.csv', index=False, sep=',')
df_media.to_csv('csv_pour_bdd/media.csv', index=False, sep=',')
df_appartenir.to_csv('csv_pour_bdd/appartenir.csv', index=False, sep=',')
df_consommer.to_csv('csv_pour_bdd/consommer.csv', index=False, sep=',')

print("\n✅ SUCCÈS ! Tes 5 fichiers CSV ont été générés dans le dossier 'csv_pour_bdd'.")