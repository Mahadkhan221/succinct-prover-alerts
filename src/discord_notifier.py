import logging
import requests


def send_discord(webhook_url: str, content: str | None = None, embeds: list[dict] | None = None) -> None:
    """
    Send a Discord webhook message.

    - For plain messages: pass content="..."
    - For rich embeds (supports markdown links): pass embeds=[{...}]
    """
    payload: dict = {}
    if content:
        payload["content"] = content
    if embeds:
        payload["embeds"] = embeds

    if not payload:
        logging.warning("Discord payload empty; nothing to send")
        return

    r = requests.post(webhook_url, json=payload, timeout=15)

    # Discord webhooks return 204 No Content on success (sometimes 200)
    if r.status_code not in (200, 204):
        logging.error("Discord webhook failed: %s %s", r.status_code, r.text)
        r.raise_for_status()

