import gradio as gr
import pandas as pd

from moteur import recommander

ACCUEIL = "Bonjour ! Je vais vous poser quelques questions pour trouver votre prochain anime."
QUESTION_ENVIE = ("De quoi avez-vous envie en ce moment ? Décrivez-le avec vos mots, "
                  "par exemple « une aventure drôle avec de la magie ».")
QUESTIONS = {
    "format": ("Plutôt une série ou un film ?", ["série", "film", "peu importe"]),
    "duree": ("Quelle longueur ? Courte : 13 épisodes maximum, moyenne : 14 à 26, longue : plus de 26.",
              ["courte", "moyenne", "longue", "peu importe"]),
    "violence": ("Voulez-vous éviter les contenus violents ?", ["non", "oui"]),
    "aimes": ("Citez un ou deux animes que vous avez aimés, séparés par des virgules (titres anglais), "
              "ou touchez « passer ».", ["passer"]),
}
ORDRE = ["envie", "format", "duree", "violence", "aimes"]
NB_BOUTONS = 4


def question(etape):
    """Le texte de la question et les réponses rapides proposées à cette étape."""
    if etape == "envie":
        return QUESTION_ENVIE, []
    if etape == "fin":
        return "Voulez-vous une autre recommandation ?", ["recommencer"]
    return QUESTIONS[etape]


def boutons(options):
    """Un bouton visible par réponse proposée, les autres cachés."""
    return [gr.Button(value=options[i], visible=True) if i < len(options) else gr.Button(visible=False)
            for i in range(NB_BOUTONS)]


def decrire(anime):
    """Le format, l'année et la note d'un anime, en une ligne."""
    if anime["type"] == "Movie":
        forme = "Film"
    elif pd.notna(anime["episodes"]):
        forme = f"Série, {int(anime['episodes'])} épisodes"
    else:
        forme = "Série"
    annee = f", {int(anime['annee'])}" if pd.notna(anime["annee"]) else ""
    return f"{forme}{annee}, note {anime['note']}/5"


def presenter(resultats, reconnus):
    """Le message du top 3, en Markdown."""
    lignes = []
    if reconnus:
        lignes.append("J'ai tenu compte de : " + ", ".join(reconnus) + ".")
    if resultats.empty:
        lignes.append("Aucun anime ne correspond à tous ces critères. Essayez avec moins de contraintes.")
    else:
        lignes.append("Voici mon top 3 :")
        for rang, (_, anime) in enumerate(resultats.iterrows(), start=1):
            genres = ", ".join(anime["genres"].split(", ")[:6])
            lignes.append(f"**{rang}. {anime['titre']}**  \n{decrire(anime)}  \n_{genres}_")
    return "\n\n".join(lignes)


def repondre(message, historique, etat):
    """Reçoit une réponse, avance d'une étape et pose la question suivante."""
    message = (message or "").strip()
    etape, reponses = etat["etape"], dict(etat["reponses"])
    if not message:
        return historique, etat, "", *boutons(question(etape)[1])
    historique = historique + [{"role": "user", "content": message}]

    if etape == "fin":
        etape, reponses = "envie", {}
    elif etape == "envie":
        reponses["envie"] = message
        etape = "format"
    elif etape == "aimes":
        aimes = [] if message.lower() == "passer" else message.split(",")
        resultats, reconnus = recommander(reponses["envie"], reponses["format"],
                                          reponses.get("duree", "peu importe"),
                                          reponses["violence"] == "oui", aimes)
        historique.append({"role": "assistant", "content": presenter(resultats, reconnus)})
        etape = "fin"
    else:
        options = QUESTIONS[etape][1]
        choix = next((o for o in options if o.startswith(message.lower())), None)
        if choix is None:
            historique.append({"role": "assistant",
                               "content": "Touchez l'une des réponses proposées : " + ", ".join(options) + "."})
            return historique, {"etape": etape, "reponses": reponses}, "", *boutons(options)
        reponses[etape] = choix
        etape = ORDRE[ORDRE.index(etape) + 1]
        if etape == "duree" and reponses["format"] == "film":
            etape = "violence"  # la longueur ne concerne pas les films

    texte, options = question(etape)
    historique.append({"role": "assistant", "content": texte})
    return historique, {"etape": etape, "reponses": reponses}, "", *boutons(options)


with gr.Blocks() as demo:
    gr.Markdown("# Quel anime commencer ?\nRépondez à quelques questions, je vous propose trois animes à voir.")
    chat = gr.Chatbot(value=[{"role": "assistant", "content": ACCUEIL + "\n\n" + QUESTION_ENVIE}],
                      show_label=False, height=480)
    with gr.Row():
        choix = [gr.Button(visible=False) for _ in range(NB_BOUTONS)]
    with gr.Row():
        saisie = gr.Textbox(placeholder="Votre réponse…", show_label=False, scale=4)
        envoyer = gr.Button("Envoyer", variant="primary", scale=1)
    etat = gr.State({"etape": "envie", "reponses": {}})

    sorties = [chat, etat, saisie, *choix]
    saisie.submit(repondre, [saisie, chat, etat], sorties)
    envoyer.click(repondre, [saisie, chat, etat], sorties)
    for bouton in choix:
        bouton.click(repondre, [bouton, chat, etat], sorties)

if __name__ == "__main__":
    demo.launch()