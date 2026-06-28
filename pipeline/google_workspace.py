#!/usr/bin/env python3
"""Connecteur Google Workspace (Sheets + Drive) du profil social-media.

Permet au pipeline d'écrire les idées du curateur dans la feuille
« Planning Editorial » (onglet 01_Idees) et de gérer l'arborescence Drive.
Authentification via compte de service (clé JSON dans config/).

Les imports Google sont paresseux : les fonctions pures (mapping) restent
testables sans les bibliothèques Google installées.
"""
from __future__ import annotations

from pipeline.config import GOOGLE_SA_KEY, GOOGLE_SHEET_ID, GOOGLE_SCOPES

# Numéro de pilier → libellé (cf. philosophy/pillars.md)
PILIERS = {
    1: "IA appliquée",
    2: "Transformation numérique industrielle",
    3: "Coulisses OmegaSoft",
    4: "Enseignement",
    5: "Vision",
}


def pilier_nom(numero) -> str:
    """Libellé du pilier à partir de son numéro (1-5), '' si inconnu."""
    try:
        return PILIERS.get(int(numero), "")
    except (TypeError, ValueError):
        return ""


def idea_to_idees_row(idea: dict, date: str, index: int) -> list[str]:
    """Mappe une idée du curateur vers une ligne de l'onglet 01_Idees.

    Colonnes : id_idee, date_creation, source, idee_brute, contexte, theme,
    audience, priorite, confidentialite, statut, commentaire_abdelilah,
    lien_ressource.
    """
    src = idea.get("source") or {}
    source_txt = f"{src.get('type', '')} {src.get('chaine', '')}".strip()
    return [
        f"{date}-{index}",                        # id_idee
        date,                                     # date_creation
        source_txt,                               # source
        idea.get("titre", ""),                    # idee_brute
        idea.get("angle", ""),                    # contexte
        pilier_nom(idea.get("pilier")),           # theme
        "",                                       # audience (non fournie)
        "",                                       # priorite
        idea.get("confidentialite", "prudent"),   # confidentialite
        "proposee",                               # statut
        "",                                       # commentaire_abdelilah
        src.get("url", ""),                       # lien_ressource
    ]


def _credentials():
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_file(
        GOOGLE_SA_KEY, scopes=GOOGLE_SCOPES)


def sheets_service():
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=_credentials(), cache_discovery=False)


def drive_service():
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=_credentials(), cache_discovery=False)


def append_ideas(ideas: list[dict], date: str) -> int:
    """Ajoute les idées dans l'onglet 01_Idees. Retourne le nb de lignes écrites."""
    if not ideas:
        return 0
    rows = [idea_to_idees_row(idea, date, i + 1) for i, idea in enumerate(ideas)]
    sheets_service().spreadsheets().values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range="01_Idees!A:L",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()
    return len(rows)
