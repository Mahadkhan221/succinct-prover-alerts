# Succinct Prover Alerts

A production-ready, containerized **one-shot Python CLI** that checks prover order activity on the Succinct Network using the official gRPC API and sends on-call style alerts to Discord.

This tool is designed to replace manual on-call checks of the Succinct Explorer with a simple, repeatable command that can be run on demand or scheduled externally (e.g. via systemd or cron).

---

## 🔍 What This Does

- Connects to the Succinct gRPC endpoint  
  `https://rpc.mainnet.succinct.xyz`
- Fetches the latest **ASSIGNED** order for a prover
- Falls back to the latest **FULFILLED** order if no assignment exists
- Sends a **single Discord alert** per run containing:
  - Order status (ASSIGNED / FULFILLED)
  - Time since last update
  - Clickable links to:
    - Order on Succinct Explorer
    - Prover on Succinct Explorer
- Uses **Discord embeds** to support Markdown-style links
- Exits immediately after sending the alert (no background polling)

---

## 🧠 Design Philosophy

- **One-shot CLI**, not a long-running service
- Easy to reason about, restart, and schedule
- No secrets committed to source control
- Configuration via environment variables
- Built directly on Succinct’s official `network.proto` and `types.proto`

---

## ✅ Requirements

- Docker
- Docker (Compose optional, not required)
---

```md
## 🚀 Quick Start

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Mahadkhan221/succinct-prover-alerts.git
cd succinct-prover-alerts

### 2️⃣ Configure environment variables
Copy the example environment file:
cp .env.example .env

Edit .env:
PROVER_ADDRESS=0xYourProverAddress
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
POLL_INTERVAL=60
HEARTBEAT_INTERVAL=3600
SEND_STARTUP_MESSAGE=true
LOG_LEVEL=INFO

### 3️⃣ Build and run the service
docker compose up -d --build
You should immediately receive a startup alert in Discord.

### 4️⃣ View logs
docker compose logs -f --tail=200

### 5️⃣ Stop or restart the service
docker compose down
docker compose restart



