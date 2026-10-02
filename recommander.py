from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

MODELE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FICHIER_VECTEURS = Path("data/embeddings.npy")

animes = pd.read_csv("data/animes.csv", dtype={"titre": str})
modele = SentenceTransformer(MODELE)

# 1. Le texte que le modèle lit pour chaque anime : titre, genres, puis résumé
textes = (animes["titre"] + ". Genres : " + animes["genres"].fillna("") + ". " + animes["resume"]).tolist()

# 2. Transformer chaque anime en vecteur (calculé une fois, puis relu depuis le fichier)
vecteurs = np.load(FICHIER_VECTEURS) if FICHIER_VECTEURS.exists() else None
if vecteurs is None or len(vecteurs) != len(animes):
    vecteurs = modele.encode(textes, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    np.save(FICHIER_VECTEURS, vecteurs)
print("Vecteurs :", vecteurs.shape)


# 3. Comparer une demande à tous les animes et garder les plus proches
def recommander(demande, n=3):
    requete = modele.encode([demande], normalize_embeddings=True)[0]
    scores = vecteurs @ requete
    meilleurs = np.argsort(-scores)[:n]
    return animes.iloc[meilleurs].assign(similarite=scores[meilleurs])


while True:
    demande = input("\nQu'avez-vous envie de regarder ? (Entrée vide pour quitter)\n> ").strip()
    if not demande:
        break
    for rang, (_, anime) in enumerate(recommander(demande).iterrows(), start=1):
        print(f"{rang}. {anime['titre']} ({anime['type']}, note {anime['note']}/5), similarité {anime['similarite']:.2f}")
        print(f"   {anime['genres']}")