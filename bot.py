import pandas as pd

from moteur import recommander


def choisir(question, options):
    """Pose une question à choix et renvoie l'option choisie."""
    print("\n" + question)
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")
    while True:
        reponse = input("> ").strip()
        if reponse.isdigit() and 1 <= int(reponse) <= len(options):
            return options[int(reponse) - 1]
        print(f"Tapez un nombre entre 1 et {len(options)}.")


def decrire(anime):
    """Une ligne lisible : format, année, note."""
    if anime["type"] == "Movie":
        forme = "film"
    elif pd.notna(anime["episodes"]):
        forme = f"série, {int(anime['episodes'])} épisodes"
    else:
        forme = "série"
    annee = f", {int(anime['annee'])}" if pd.notna(anime["annee"]) else ""
    return f"{anime['titre']} ({forme}{annee}), note {anime['note']}/5"


print("Bonjour ! Je vais vous poser quelques questions pour trouver votre prochain anime.")
while True:
    envie = input("\nDe quoi avez-vous envie en ce moment ? Décrivez-le avec vos mots.\n> ").strip()
    format_ = choisir("Plutôt une série ou un film ?", ["série", "film", "peu importe"])
    duree = "peu importe"
    if format_ != "film":
        duree = choisir("Quelle longueur ? (courte : 13 épisodes max, moyenne : 14 à 26, longue : plus de 26)",
                        ["courte", "moyenne", "longue", "peu importe"])
    sans_violence = choisir("Voulez-vous éviter les contenus violents ?", ["non", "oui"]) == "oui"
    aimes = input("\nCitez un ou deux animes que vous avez aimés, séparés par des virgules "
                  "(titres anglais), ou appuyez sur Entrée pour passer.\n> ").split(",")

    resultats, reconnus = recommander(envie, format_, duree, sans_violence, aimes)
    if reconnus:
        print("\nJ'ai tenu compte de :", ", ".join(reconnus))
    if resultats.empty:
        print("\nAucun anime ne correspond à tous ces critères. Essayez avec moins de contraintes.")
    else:
        print("\nVoici mon top 3 :")
        for rang, (_, anime) in enumerate(resultats.iterrows(), start=1):
            print(f"{rang}. {decrire(anime)}")
            print(f"   {anime['genres']}")

    if choisir("Voulez-vous une autre recommandation ?", ["oui", "non"]) == "non":
        print("Bon visionnage !")
        break