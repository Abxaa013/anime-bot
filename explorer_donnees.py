import pandas as pd
from datasets import load_dataset

# 1. Télécharger le jeu de données depuis le Hub (mis en cache après la première fois)
ds = load_dataset("wykonos/anime", split="train")
print(ds)

# 2. Un anime tel qu'il est stocké : un dictionnaire colonne -> valeur
premier = ds[0]
for cle in ["Name", "Type", "Episodes", "Tags", "Rating", "Release_year", "Description"]:
    print(f"{cle} : {premier[cle]}")

# 3. Passer en tableau pandas pour explorer plus facilement
df = ds.to_pandas()
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 50)
print(df[["Name", "Type", "Episodes", "Rating"]].head(10))

print("\nTypes :")
print(df["Type"].value_counts())

sans_resume = df["Description"].isna() | df["Description"].str.contains("No synopsis", na=False)
print("\nAnimes sans vrai résumé :", sans_resume.sum(), "sur", len(df))