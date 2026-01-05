import os
import time
import signal
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.grpc_client import fetch_latest_assigned_or_fulfilled
from src.discord_notifier import send_discord

# Load environment variables
load_dotenv()

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Config
PROVER = os.getenv("PROVER_ADDRESS")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
ENDPOINT = os.getenv("GRPC_ENDPOINT", "https://rpc.mainnet.succinct.xyz")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "3600"))
SEND_STARTUP = os.getenv("SEND_STARTUP_MESSAGE", "false").lower() == "true"

if not PROVER or not WEBHOOK:
    raise RuntimeError("PROVER_ADDRESS and DISCORD_WEBHOOK_URL must be set")

# Timezone
PKT = ZoneInfo("Asia/Karachi")

running = True
last_seen_key = None
last_heartbeat_ts = 0


# Graceful shutdown
def shutdown_handler(sig, frame):
    global running
    logging.info("Shutdown signal received, exiting...")
    running = False


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# Helpers
def epoch_to_pkt(epoch: int | None) -> datetime | None:
    if not epoch:
        return None
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).astimezone(PKT)
    except Exception:
        return None


def fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    return dt.strftime("%Y-%m-%d %H:%M:%S PKT")


def time_ago(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    now = datetime.now(PKT)
    delta = now - dt
    secs = int(delta.total_seconds())
    if secs < 0:
        secs = 0
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)

    out = []
    if days:
        out.append(f"{days}d")
    if hours or days:
        out.append(f"{hours}h")
    out.append(f"{mins}m")
    return " ".join(out) + " ago"


def short_addr(a: str | None) -> str:
    if not a:
        return "unknown"
    a = a.lower().replace("0x", "")
    return "0x" + a[:6] + "…" + a[-4:]


def dedupe_key(result: dict) -> str:
    d = result.get("details", {}) or {}
    return f"{result.get('status')}:{result.get('id')}:{d.get('updated_at', 0)}"


def format_message(result: dict, prefix: str) -> str:
    d = result.get("details", {}) or {}

    created = epoch_to_pkt(d.get("created_at"))
    updated = epoch_to_pkt(d.get("updated_at"))

    lines = [
        f"{prefix} **Latest {result['status']} order**",
        f"**Prover:** `{PROVER}`",
        f"**Order ID:** `{result['id']}`",
        "",
        f"**Last Update:** {fmt_dt(updated)} • **{time_ago(updated)}**",
        f"**Created:** {fmt_dt(created)} • **{time_ago(created)}**",
        "",
        f"**Requester:** `{short_addr(d.get('requester'))}`",
        f"**Fulfiller:** `{short_addr(d.get('fulfiller'))}`",
    ]

    if d.get("program_public_uri"):
        lines.append(f"**Program:** {d['program_public_uri']}")
    if d.get("stdin_public_uri"):
        lines.append(f"**Stdin:** {d['stdin_public_uri']}")

    return "\n".join(lines)


# Startup message
if SEND_STARTUP:
    send_discord(
        WEBHOOK,
        f"✅ Prover monitor started for `{PROVER}` (poll={POLL_INTERVAL}s, heartbeat={HEARTBEAT_INTERVAL}s)",
    )

logging.info("Monitoring prover=%s poll=%ss heartbeat=%ss", PROVER, POLL_INTERVAL, HEARTBEAT_INTERVAL)

# Main loop
while running:
    now = int(time.time())

    try:
        result = fetch_latest_assigned_or_fulfilled(ENDPOINT, PROVER)

        if result:
            key = dedupe_key(result)

            # Send on change
            if key != last_seen_key:
                send_discord(WEBHOOK, format_message(result, "🚨"))
                last_seen_key = key
                logging.info("Alert sent (%s)", key)
            else:
                logging.info("No change (%s)", key)

            # Hourly heartbeat
            if now - last_heartbeat_ts >= HEARTBEAT_INTERVAL:
                send_discord(WEBHOOK, format_message(result, "🕐"))
                last_heartbeat_ts = now
                logging.info("Heartbeat sent")

        else:
            logging.info("No assigned/fulfilled orders found")
            if now - last_heartbeat_ts >= HEARTBEAT_INTERVAL:
                send_discord(
                    WEBHOOK,
                    f"🕐 **Hourly update**\nNo assigned or fulfilled orders for `{PROVER}`.",
                )
                last_heartbeat_ts = now

    except Exception:
        logging.exception("Polling error")

    # Sleep gracefully
    for _ in range(POLL_INTERVAL):
        if not running:
            break
        time.sleep(1)

logging.info("Prover monitor stopped")

