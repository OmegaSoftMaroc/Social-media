"""Paramètres du pipeline (chaînes, cadence, nombre d'idées).
À revalider avec Abdelilah avant le premier run réel.
"""

# handle YouTube → channel_id (résolu une fois, hardcodé pour éviter yt-dlp)
KNOWN_IDS = {
    "@nateherk": "UC2ojq-nuP8ceeHqiroeKhBA",
    "@adev_cpl": "UCoWs1E6OLTqv6BMUjgZENMw",
    "@ParlonsIATech": "UCrRlS6QE1DsKnLDksvaBkKA",
    "@Shubham_Sharma": "UCLKx4-_XO5sR0AO0j8ye7zQ",
}

# Chaînes suivies (orientées IA/tech → pilier 1 majoritaire)
CHANNELS = list(KNOWN_IDS.keys())

# Nombre d'idées proposées par run (min, max)
IDEAS_PER_RUN = (5, 7)

# Fenêtre de récence RSS (heures)
RECENCY_HOURS = 25

# --- Google Workspace (feuille « Planning Editorial » + Drive) ---------------
# Clé du compte de service (relative au cwd = racine du profil au runtime).
GOOGLE_SA_KEY = "config/google-service-account.json"
# Feuille « Omega Media AI - Planning Editorial ».
GOOGLE_SHEET_ID = "13TXa567fJnd3rUyDwl_sUMMHVlY_HUUPB5bW5C5-XjQ"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# --- Génération visuelle (Ideogram) -----------------------------------------
# Clé lue depuis l'environnement / config/.env : IDEOGRAM_API_KEY
IDEOGRAM_ENDPOINT = "https://api.ideogram.ai/v1/ideogram-v3/generate"
VISUAL_ASPECT = "4x5"  # portrait LinkedIn 1080x1350
# Identité visuelle de marque (à ajuster avec Abdelilah : couleurs réelles OmegaSoft)
BRAND_STYLE = (
    "professional B2B tech illustration, clean and modern, minimal, "
    "dark navy blue and teal palette with a bright energetic accent color, "
    "subtle geometric shapes, generous negative space, high quality"
)
# Photo d'Abdelilah à incruster en rond, coin bas-droite (Drive: Ressources/image/akahji.png)
BRAND_PHOTO_FILE_ID = "1VxNIKwm0NPfuzdQFhpBFSOTBuafRaXtW"
# Exclusions Ideogram (negative_prompt) : pas de personnage ni de texte sur le fond
VISUAL_NEGATIVE = (
    "person, people, human, face, portrait, man, woman, silhouette, "
    "text, letters, words, typography, captions, watermark, signature, logo"
)
