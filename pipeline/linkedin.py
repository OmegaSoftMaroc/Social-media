#!/usr/bin/env python3
"""Connecteur LinkedIn — OAuth + publication sur le profil personnel.

Flux : URL d'autorisation → code → access_token (stocké dans config/.env)
→ URN du membre (/userinfo) → publication via /v2/ugcPosts.

⚠️ La publication n'a lieu qu'APRÈS validation d'Abdelilah (jamais automatique).
"""
from __future__ import annotations

CONFIG_ENV = "/opt/hermes/data/profiles/social-media/config/.env"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
REGISTER_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"


def _env() -> dict:
    from dotenv import dotenv_values
    return dotenv_values(CONFIG_ENV)


def exchange_code(code: str) -> dict:
    """Échange le code d'autorisation contre un access_token (JSON LinkedIn)."""
    import requests
    c = _env()
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": c["LINKEDIN_CLIENT_ID"],
        "client_secret": c["LINKEDIN_CLIENT_SECRET"],
        "redirect_uri": c.get("LINKEDIN_REDIRECT_URI", "https://localhost/callback"),
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_person_urn(access_token: str) -> str:
    """URN du membre via /userinfo (champ `sub`)."""
    import requests
    r = requests.get(USERINFO_URL,
                     headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    r.raise_for_status()
    return "urn:li:person:" + r.json()["sub"]


def publish_text(text: str, access_token: str | None = None,
                 person_urn: str | None = None) -> dict:
    """Publie un post texte sur le profil (visibilité PUBLIC). APRÈS validation."""
    import requests
    c = _env()
    token = access_token or c.get("LINKEDIN_ACCESS_TOKEN")
    urn = person_urn or c.get("LINKEDIN_PERSON_URN")
    if not token or not urn:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN / LINKEDIN_PERSON_URN manquant")
    body = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = requests.post(POSTS_URL, json=body, timeout=30, headers={
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    })
    r.raise_for_status()
    return {"status": r.status_code, "post_id": r.headers.get("x-restli-id")}


def _register_image_upload(token: str, urn: str):
    """Enregistre un upload image, retourne (upload_url, asset_urn)."""
    import requests
    body = {"registerUploadRequest": {
        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
        "owner": urn,
        "serviceRelationships": [
            {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
        ],
    }}
    r = requests.post(REGISTER_URL, json=body, timeout=30, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r.raise_for_status()
    val = r.json()["value"]
    upload_url = val["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    return upload_url, val["asset"]


def publish_image_post(text: str, image_path: str, access_token: str | None = None,
                       person_urn: str | None = None) -> dict:
    """Publie un post avec image (visibilité PUBLIC). APRÈS validation."""
    import requests
    c = _env()
    token = access_token or c.get("LINKEDIN_ACCESS_TOKEN")
    urn = person_urn or c.get("LINKEDIN_PERSON_URN")
    if not token or not urn:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN / LINKEDIN_PERSON_URN manquant")

    upload_url, asset = _register_image_upload(token, urn)
    with open(image_path, "rb") as fh:
        requests.put(upload_url, data=fh.read(),
                     headers={"Authorization": f"Bearer {token}"}, timeout=60).raise_for_status()

    body = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{"status": "READY", "media": asset,
                           "title": {"text": "Visuel OmegaSoft"}}],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = requests.post(POSTS_URL, json=body, timeout=30, headers={
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    })
    r.raise_for_status()
    return {"status": r.status_code, "post_id": r.headers.get("x-restli-id")}


def _register_video_upload(token: str, urn: str):
    """Enregistre un upload vidéo, retourne (upload_url, asset_urn)."""
    import requests
    body = {"registerUploadRequest": {
        "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
        "owner": urn,
        "serviceRelationships": [
            {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
        ],
    }}
    r = requests.post(REGISTER_URL, json=body, timeout=30, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r.raise_for_status()
    val = r.json()["value"]
    upload_url = val["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    return upload_url, val["asset"]


def publish_video_post(text: str, video_path: str, access_token: str | None = None,
                       person_urn: str | None = None) -> dict:
    """Publie un post vidéo (PUBLIC). APRÈS validation explicite uniquement."""
    import requests
    c = _env()
    token = access_token or c.get("LINKEDIN_ACCESS_TOKEN")
    urn = person_urn or c.get("LINKEDIN_PERSON_URN")
    if not token or not urn:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN / LINKEDIN_PERSON_URN manquant")

    upload_url, asset = _register_video_upload(token, urn)
    with open(video_path, "rb") as fh:
        requests.put(upload_url, data=fh.read(), timeout=300,
                     headers={"Authorization": f"Bearer {token}"}).raise_for_status()

    body = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "VIDEO",
                "media": [{"status": "READY", "media": asset,
                           "title": {"text": "Vidéo OmegaSoft"}}],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    r = requests.post(POSTS_URL, json=body, timeout=30, headers={
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    })
    r.raise_for_status()
    return {"status": r.status_code, "post_id": r.headers.get("x-restli-id")}
