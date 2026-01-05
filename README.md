# Succinct Prover Alerts

A production-ready, containerized Python application that monitors the **Succinct Network gRPC API** for prover order activity and sends **on-call style alerts to Discord**.

This service continuously checks which order is **assigned** to a prover.  
If no assigned order exists, it automatically falls back to the **latest fulfilled order**.

---

## 🔍 What This Does

- Connects to the Succinct gRPC endpoint: `https://rpc.mainnet.succinct.xyz`
- Fetches the **latest ASSIGNED order** for a prover
- Falls back to the **latest FULFILLED order** if no assignment exists
- Sends alerts to Discord when:
  - A new order is assigned
  - A new order is fulfilled
  - An existing order is updated
- Sends an **hourly heartbeat** message for on-call style monitoring
- Formats timestamps in **Pakistan Time (PKT)** and shows **time since last update**
- Runs fully via **Docker Compose**

---

## ✅ Requirements

- Docker
- Docker Compose (v2)

---

## 🚀 Quick Start

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Mahadkhan221/succinct-prover-alerts.git
cd succinct-prover-alerts
Configure environment variables

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



