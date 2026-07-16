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
    # 'drive' seul suffit (couvre aussi l'API Sheets) et correspond au scope
    # autorisé dans la délégation domain-wide.
    "https://www.googleapis.com/auth/drive",
]
# Délégation à l'échelle du domaine : le compte de service agit AU NOM de cet
# utilisateur (fichiers créés lui appartiennent). Mettre "" pour désactiver.
GOOGLE_IMPERSONATE = "a.kahaji@omegasoft.ma"
# Dossier racine des sources (= 01_Resources : Articles, Videos, Recherche… et Visuels).
# ATTENTION : fourre-tout d'assets bruts — NE PAS y déposer les livrables à valider.
GOOGLE_SOURCES_PARENT = "1CLXIjvxD3Y5jolA9FcX9WTfM_k46Bum4"
# Espace d'échange convenu « Omega Media AI - Social Media » et ses dossiers d'étape.
# Un livrable rendu (vidéo/visuel) prêt à être revu par Abdelilah va dans 04_Validation ;
# validé → 05_Final ; publié → 06_Published. (cf. mémoire feedback-drive-dossier-echange)
GOOGLE_WORKSPACE_PARENT = "10l9rc-tx0FwoDFEqtPRLxxQ7tusmxoc2"
GOOGLE_VALIDATION_FOLDER = "18F5OETXbo_OjDm-LfxycqPVx6F42PXFL"  # 04_Validation
GOOGLE_FINAL_FOLDER = "1mSuslsW-HKf6J2Cg7mt1Xxe26FYyMgMg"       # 05_Final
GOOGLE_PUBLISHED_FOLDER = "18fJtf718n8YnMIjpxnSaMuORiMTXlyr-"   # 06_Published

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

# --- Vidéo (ElevenLabs + HeyGen) ----------------------------------------------
# Clés dans config/.env : ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
#                         HEYGEN_API_KEY, HEYGEN_AVATAR_ID
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
HEYGEN_UPLOAD_URL = "https://upload.heygen.com/v1/asset"
HEYGEN_GENERATE_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_URL = "https://api.heygen.com/v1/video_status.get"

# Formats de sortie : calibrage script (mots) + dimensions vidéo
VIDEO_FORMATS = {
    "linkedin": {"dimension": {"width": 1280, "height": 720},
                 "target_words": (150, 220)},   # ~60-90 s parlées
    "short": {"dimension": {"width": 720, "height": 1280},
              "target_words": (70, 110)},        # ~30-45 s, 9:16
}
VIDEO_POLL_S = 20       # intervalle de polling HeyGen
VIDEO_TIMEOUT_S = 900   # 15 min max par vidéo
