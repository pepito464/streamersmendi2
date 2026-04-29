"""
Logger : récupère le nombre de followers Twitch et de membres Telegram
et ajoute une ligne au CSV à chaque exécution.
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

# --- Configuration via variables d'environnement (GitHub Secrets) ---
TWITCH_CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]
TWITCH_USERNAME = os.environ.get("TWITCH_USERNAME", "omendigotv")
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CSV_PATH = Path("data/log.csv")
LISBON = ZoneInfo("Europe/Lisbon")


def get_twitch_app_token() -> str:
    """Échange client_id + secret contre un app access token (valide ~60 jours)."""
    r = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def get_twitch_user_id(token: str, username: str) -> str:
    r = requests.get(
        "https://api.twitch.tv/helix/users",
        params={"login": username},
        headers={
            "Client-Id": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()["data"]
    if not data:
        raise RuntimeError(f"Utilisateur Twitch introuvable: {username}")
    return data[0]["id"]


def get_twitch_followers(token: str, broadcaster_id: str) -> int:
    """Total followers : fonctionne sans scope mod, le champ 'total' est public."""
    r = requests.get(
        "https://api.twitch.tv/helix/channels/followers",
        params={"broadcaster_id": broadcaster_id},
        headers={
            "Client-Id": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        },
        timeout=15,
    )
    r.raise_for_status()
    return int(r.json()["total"])


def get_telegram_members(bot_token: str, chat_id: str) -> int:
    r = requests.get(
        f"https://api.telegram.org/bot{bot_token}/getChatMemberCount",
        params={"chat_id": chat_id},
        timeout=15,
    )
    r.raise_for_status()
    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Erreur Telegram: {payload}")
    return int(payload["result"])


def append_row(row: dict) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    now_utc = datetime.now(tz=ZoneInfo("UTC"))
    now_lisbon = now_utc.astimezone(LISBON)

    try:
        token = get_twitch_app_token()
        broadcaster_id = get_twitch_user_id(token, TWITCH_USERNAME)
        followers = get_twitch_followers(token, broadcaster_id)
    except Exception as exc:
        print(f"[ERREUR Twitch] {exc}", file=sys.stderr)
        followers = ""

    try:
        members = get_telegram_members(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    except Exception as exc:
        print(f"[ERREUR Telegram] {exc}", file=sys.stderr)
        members = ""

    row = {
        "timestamp_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_lisbon": now_lisbon.strftime("%Y-%m-%d %H:%M:%S"),
        "twitch_followers": followers,
        "telegram_members": members,
    }
    append_row(row)
    print(f"OK | {row}")

    # Code retour non-nul si les deux sources ont échoué
    return 0 if (followers != "" or members != "") else 1


if __name__ == "__main__":
    sys.exit(main())
