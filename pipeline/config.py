"""Paramètres du pipeline (chaînes, cadence, nombre d'idées).
À revalider avec Abdelilah avant le premier run réel.
"""

# handle YouTube → channel_id (résolu une fois, hardcodé pour éviter yt-dlp)
KNOWN_IDS = {
    "@nateherk": "UCBcRF18a7Qf58cCRy5xuWwQ",
    "@adev_cpl": "UCnXNIFvxP_x_LnJQNlOJFBg",
    "@ParlonsIATech": "UCBt6l-PqxDKVHcBTuEZASpw",
    "@Shubham_Sharma": "UCIz_lJqEoBT_yFxl0Y8HIEQ",
}

# Chaînes suivies (orientées IA/tech → pilier 1 majoritaire)
CHANNELS = list(KNOWN_IDS.keys())

# Nombre d'idées proposées par run (min, max)
IDEAS_PER_RUN = (3, 5)

# Fenêtre de récence RSS (heures)
RECENCY_HOURS = 25
