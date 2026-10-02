# Anime-bot : quel anime commencer ?

Un chatbot qui pose quelques questions sur vos envies, puis propose un top 3 d'animes à voir. Il est construit en Python, avec des modèles Hugging Face et une interface Gradio.

**Essayer l'appli :** https://huggingface.co/spaces/abxaa/anime-bot

## Comment ça marche

1. Le bot pose ses questions : votre envie du moment (en texte libre), série ou film, la longueur, si vous voulez éviter les contenus violents, et un ou deux animes que vous avez aimés.
2. Un modèle d'embeddings transforme votre envie, et chaque résumé d'anime, en un vecteur de 384 nombres. Deux textes de sens proche donnent des vecteurs proches, même dans deux langues différentes : une demande en français retrouve des résumés en anglais.
3. Les animes que vous avez aimés enrichissent votre demande : leurs vecteurs sont moyennés avec celui de votre envie.
4. Chaque anime reçoit un score : 85 % de similarité avec votre demande, 15 % de note des spectateurs. Vos critères (format, longueur, violence) écartent les animes qui ne conviennent pas.
5. Les trois meilleurs scores forment le top 3.

## Technologies

- **Python** 3.10 ou plus récent
- **Hugging Face** : la bibliothèque `datasets` pour les données, et `sentence-transformers` pour le modèle [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- **Gradio 6** pour l'interface de chat
- **pandas** et **NumPy** pour la préparation des données et les calculs

## Données

Les animes viennent du jeu de données [wykonos/anime](https://huggingface.co/datasets/wykonos/anime) : environ 18 500 animes avec leur résumé, leurs genres, une note sur 5, le type et le nombre d'épisodes. Le script `preparer_donnees.py` le nettoie :

- il garde les séries TV, les séries web et les films notés au moins 3,5/5 ;
- il retire les résumés absents ou trop courts, et nettoie les autres ;
- il sépare les vrais genres des avertissements de contenu ;
- il écarte les suites (« Season 2 », « Part II »…), pour ne conseiller que des animes à commencer.

Le résultat est enregistré dans `data/animes.csv`, et les vecteurs calculés dans `data/embeddings.npy`.

## Structure du projet

| Fichier | Rôle |
| --- | --- |
| `app.py` | L'interface Gradio : la conversation et les boutons de réponse |
| `moteur.py` | Le moteur : modèle, vecteurs, filtres et calcul du top 3 |
| `preparer_donnees.py` | Téléchargement et nettoyage du jeu de données |
| `bot.py` | La même conversation, dans le terminal |
| `explorer_donnees.py` | Premier coup d'œil aux données brutes |
| `diagnostic.py` | Vérification des données, critère par critère |
| `verif.py` | Vérification de l'installation des bibliothèques |
| `deployer.py` | Envoi de l'appli sur le Space Hugging Face |
| `requirements.txt` | Bibliothèques à installer sur le Space |
| `data/` | Données nettoyées et vecteurs précalculés |

## Lancer le projet sur son ordinateur

```powershell
git clone https://github.com/VOTRE-PSEUDO-GITHUB/anime-bot.git
cd anime-bot
python -m venv .venv
.venv\Scripts\Activate.ps1        # macOS / Linux : source .venv/bin/activate
pip install torch transformers sentence-transformers datasets gradio
python app.py
```

Ouvrez ensuite http://127.0.0.1:7860 dans votre navigateur. Au premier lancement, le modèle (environ 500 Mo) est téléchargé.

Pour régénérer les données, lancez `python preparer_donnees.py`. Les vecteurs sont recalculés automatiquement au lancement suivant.

## Mise en ligne

L'appli tourne sur un Space Hugging Face (SDK Gradio, matériel CPU Basic). Depuis 2026, héberger un Space Gradio demande un abonnement Hugging Face PRO. Pour publier une nouvelle version :

```powershell
hf auth login        # une seule fois, avec une clé d'accès de type « Write »
python deployer.py
```

## Pistes d'amélioration

- Comprendre les réponses libres avec un modèle de classification « zero-shot »
- Expliquer chaque recommandation en français avec un petit modèle de langage (Qwen)
- Reconnaître aussi les titres japonais des animes aimés
- Ajuster le poids de la note (`POIDS_NOTE` dans `moteur.py`) et le seuil de note (`SEUIL_NOTE` dans `preparer_donnees.py`)

## Crédits

- Données : [wykonos/anime](https://huggingface.co/datasets/wykonos/anime) sur Hugging Face
- Modèle : [sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
