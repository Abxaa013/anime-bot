"""Moteur de recommandation : données, modèle d'embeddings et calcul du top 3."""
import difflib
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

MODELE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FICHIER_ANIMES = Path("data/animes.csv")
FICHIER_VECTEURS = Path("data/embeddings.npy")
POIDS_NOTE = 0.15  # part de la note dans le score final (0 = seulement le sens du texte)

# 1. Charger les animes et le modèle
animes = pd.read_csv(FICHIER_ANIMES, dtype={"titre": str})
animes["genres"] = animes["genres"].fillna("")
animes["avertissements"] = animes["avertissements"].fillna("")
modele = SentenceTransformer(MODELE)

# 2. Vecteurs des animes (calculés une fois, puis relus depuis le fichier)
textes = (animes["titre"] + ". Genres : " + animes["genres"] + ". " + animes["resume"]).tolist()
vecteurs = np.load(FICHIER_VECTEURS) if FICHIER_VECTEURS.exists() else None
if vecteurs is None or len(vecteurs) != len(animes):
    vecteurs = modele.encode(textes, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    np.save(FICHIER_VECTEURS, vecteurs)

# Note ramenée entre 0 (la plus basse gardée) et 1 (la meilleure)
notes = animes["note"]
note_normalisee = ((notes - notes.min()) / (notes.max() - notes.min())).to_numpy()
titres_minuscules = animes["titre"].str.lower().tolist()


def trouver_animes(noms):
    """Retrouve dans la liste les animes cités par l'utilisateur, même mal orthographiés."""
    trouves = []
    for nom in noms:
        nom = nom.strip().lower()
        if not nom:
            continue
        # D'abord les titres qui contiennent le nom tapé : on garde le plus court (souvent l'original)
        contiennent = [i for i, titre in enumerate(titres_minuscules) if nom in titre]
        if contiennent:
            trouves.append(min(contiennent, key=lambda i: len(titres_minuscules[i])))
            continue
        # Sinon, le titre le plus ressemblant (tolère les fautes de frappe)
        proches = difflib.get_close_matches(nom, titres_minuscules, n=1, cutoff=0.6)
        if proches:
            trouves.append(titres_minuscules.index(proches[0]))
    return list(dict.fromkeys(trouves))  # sans doublons, dans l'ordre


def recommander(envie, format_="peu importe", duree="peu importe", sans_violence=False, aimes=(), n=3):
    """Renvoie les n animes conseillés et la liste des animes aimés qui ont été reconnus."""
    # 1. Vecteur de la demande, enrichi des animes aimés (moyenne des vecteurs)
    vecteur = modele.encode([envie or "un très bon anime"], normalize_embeddings=True)[0]
    deja_vus = trouver_animes(aimes)
    if deja_vus:
        vecteur = vecteur + vecteurs[deja_vus].mean(axis=0)
        vecteur = vecteur / np.linalg.norm(vecteur)
    similarite = vecteurs @ vecteur
    score = (1 - POIDS_NOTE) * similarite + POIDS_NOTE * note_normalisee

    # 2. Filtres selon les réponses (un tableau de vrai/faux, un par anime)
    garder = np.ones(len(animes), dtype=bool)
    if format_ == "série":
        garder &= animes["type"].isin(["TV", "Web"]).to_numpy()
    elif format_ == "film":
        garder &= (animes["type"] == "Movie").to_numpy()
    episodes = animes["episodes"]
    if duree == "courte":
        garder &= (episodes <= 13).to_numpy()
    elif duree == "moyenne":
        garder &= ((episodes > 13) & (episodes <= 26)).to_numpy()
    elif duree == "longue":
        garder &= (episodes > 26).to_numpy()
    if sans_violence:
        garder &= ~animes["avertissements"].str.contains("Violence|Gore", case=False).to_numpy()
    garder[deja_vus] = False  # ne pas reconseiller ce que la personne a déjà vu

    # 3. Les meilleurs scores parmi les animes gardés
    score = np.where(garder, score, -np.inf)
    meilleurs = [i for i in np.argsort(-score)[:n] if np.isfinite(score[i])]
    resultats = animes.iloc[meilleurs].assign(similarite=similarite[meilleurs])
    return resultats, [animes["titre"].iloc[i] for i in deja_vus]