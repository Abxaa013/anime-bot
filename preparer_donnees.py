import re
from pathlib import Path

import pandas as pd
from datasets import load_dataset

SEUIL_NOTE = 3.5                      # note minimale (sur 5) pour garder un anime
TYPES_GARDES = ["TV", "Movie", "Web"]  # séries TV, films, séries web

# 1. Charger les données et garder les colonnes utiles, renommées en français
df = load_dataset("wykonos/anime", split="train").to_pandas()
depart = len(df)
df = df[["Name", "Type", "Episodes", "Release_year", "Rating", "Tags", "Content_Warning", "Description"]].copy()
df = df.rename(columns={
    "Name": "titre", "Type": "type", "Episodes": "episodes", "Release_year": "annee",
    "Rating": "note", "Tags": "tags", "Content_Warning": "avertissements", "Description": "resume",
})


# 2. Nettoyer les résumés : guillemets autour du texte, caractères spéciaux restés en clair
def nettoyer_resume(texte):
    if not isinstance(texte, str):
        return ""
    texte = texte.strip().strip("'\"")
    for code, remplacement in [("\\xa0", " "), ("\xa0", " "), ("\\'", "'"), ('\\"', '"'), ("\\n", " ")]:
        texte = texte.replace(code, remplacement)
    return re.sub(r"\s+", " ", texte).strip()


df["resume"] = df["resume"].apply(nettoyer_resume)


# 3. Séparer les vrais genres des avertissements de contenu (mélangés dans « Tags »)
def en_liste(texte):
    if not isinstance(texte, str):
        return []
    return [morceau.strip() for morceau in texte.split(",") if morceau.strip()]


def genres_seuls(ligne):
    avertissements = set(en_liste(ligne["avertissements"]))
    return ", ".join(t for t in en_liste(ligne["tags"]) if t not in avertissements)


df["genres"] = df.apply(genres_seuls, axis=1)
df["avertissements"] = df["avertissements"].apply(lambda t: ", ".join(en_liste(t)))

# 4. Filtrer : bons animes, vrai résumé, pas de suites
SUITE_TITRE = r"\b(?:Seasons?|Part(?!-)|Arc|Movie|Specials?|OVA|Recaps?|2nd|3rd|\d+th|II+)\b|\s[2-9]$"
SUITE_RESUME = (r"^(?:Continuation|Sequel|The (?:second|third|fourth|fifth|final)"
                r"|(?:Second|Third|Fourth|Fifth|Sixth|Final) (?:season|arc))")

# Uniformiser le type : espaces en trop, majuscules, précisions ajoutées
def normaliser_type(texte):
    texte = str(texte).strip().lower()
    if texte.startswith("movie"):
        return "Movie"
    if texte.startswith("web"):
        return "Web"
    if texte.startswith("tv") and "special" not in texte:
        return "TV"
    return "Autre"


df["type"] = df["type"].apply(normaliser_type)
df = df[df["type"].isin(TYPES_GARDES)]
df = df[df["note"] >= SEUIL_NOTE]
df = df[df["resume"].str.len() >= 100]
df = df[~df["resume"].str.contains("No synopsis", case=False)]
df = df[~df["genres"].str.contains("Hentai", case=False)]
df = df[~df["titre"].str.contains(SUITE_TITRE, regex=True)]
df = df[~df["resume"].str.contains(SUITE_RESUME, case=False, regex=True)]
df = df.drop_duplicates(subset="titre").copy()

# 5. Mettre en forme et enregistrer
df["episodes"] = df["episodes"].round().astype("Int64")
df["annee"] = df["annee"].round().astype("Int64")
df = df.sort_values("note", ascending=False).reset_index(drop=True)
df = df[["titre", "type", "episodes", "annee", "note", "genres", "avertissements", "resume"]]

Path("data").mkdir(exist_ok=True)
df.to_csv("data/animes.csv", index=False, encoding="utf-8")

print(f"{len(df)} animes gardés sur {depart}")
print(df[["titre", "type", "episodes", "note"]].head(15).to_string(index=False))
print("\nGenres du premier :", df.loc[0, "genres"])
print("Résumé du premier :", df.loc[0, "resume"][:300])