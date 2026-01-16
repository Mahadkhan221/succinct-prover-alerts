import os
import time
import logging
from dotenv import load_dotenv

from src.grpc_client import fetch_latest_assigned_or_fulfilled
from src.discord_notifier import send_discord

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)

PROVER = os.getenv("PROVER_ADDRESS")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
ENDPOINT = os.getenv("GRPC_ENDPOINT", "https://rpc.mainnet.succinct.xyz")

ORDER_EXPLORER_BASE = "https://explorer.succinct.xyz/order"
PROVER_EXPLORER_BASE = "https://explorer.succinct.xyz/prover"

if not PROVER or not WEBHOOK:
    raise SystemExit("PROVER_ADDRESS and DISCORD_WEBHOOK_URL must be set")


def mins_ago(epoch: int | None) -> str:
    if not epoch:
        return "unknown"

    now = int(time.time())  # epoch seconds (UTC)
    diff = max(0, now - int(epoch))
    mins = diff // 60

    if mins < 60:
        return f"{mins} mins ago"

    hours = mins // 60
    rem = mins % 60
    return f"{hours}h {rem}m ago"


def build_embed(result: dict) -> list[dict]:
    status = result.get("status", "UNKNOWN")
    details = result.get("details", {}) or {}

    order_id = details.get("request_id")
    ts = details.get("updated_at") or details.get("created_at")
    last_order = mins_ago(ts)

    prover_link = f"{PROVER_EXPLORER_BASE}/{PROVER}"
    order_link = f"{ORDER_EXPLORER_BASE}/{order_id}" if order_id else None

    # Markdown links work inside embeds
    order_value = f"[View order]({order_link})" if order_link else "N/A"
    prover_value = f"[View prover]({prover_link})"

    embed = {
        "title": "Succinct Prover",
        "description": f"Status: **{status}**\nLast order: **{last_order}**",
        "fields": [
            {"name": "Order", "value": order_value, "inline": True},
            {"name": "Prover", "value": prover_value, "inline": True},
        ],
    }
    return [embed]


def main() -> int:
    logging.info("Running one-shot prover check")

    result = fetch_latest_assigned_or_fulfilled(ENDPOINT, PROVER)

    if not result:
        prover_link = f"{PROVER_EXPLORER_BASE}/{PROVER}"
        embeds = [{
            "title": "Succinct Prover",
            "description": "No ASSIGNED or FULFILLED orders found",
            "fields": [{"name": "Prover", "value": f"[View prover]({prover_link})", "inline": True}],
        }]
        send_discord(WEBHOOK, embeds=embeds)
        logging.info("No orders found")
        return 0

    embeds = build_embed(result)
    send_discord(WEBHOOK, embeds=embeds)
    logging.info("Alert sent: %s", result.get("status"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

