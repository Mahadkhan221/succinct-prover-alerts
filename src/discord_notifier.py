import requests
import logging

def send_discord(webhook_url, content):
    payload = {"content": content}
    r = requests.post(webhook_url, json=payload, timeout=10)
    if r.status_code >= 300:
        logging.error("Discord webhook failed: %s %s", r.status_code, r.text)
