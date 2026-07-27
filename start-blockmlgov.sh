#!/bin/bash
# ============================================
#   BlockML-Gov — Script de démarrage complet
#   Portable : fonctionne quel que soit l'utilisateur
# ============================================

# Détection automatique du répertoire du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "============================================"
echo "  🚀 BlockML-Gov — Démarrage complet"
echo "  📁 Répertoire : $PROJECT_DIR"
echo "============================================"

# ── Étape 1 : Réseau Hyperledger Fabric ──────
echo ">>> Étape 1 — Réseau Hyperledger Fabric..."
cd "$PROJECT_DIR/blockchain/network"
docker compose -f docker-compose-fabric.yml up -d
echo "⏳ Attente Fabric (20s)..."
sleep 20

# ── Étape 1b : /etc/hosts ────────────────────
echo ">>> Étape 1b — Configuration /etc/hosts sautée (déjà configurée manuellement)"


# ── Étape 2 : Stack applicative ──────────────
echo ">>> Étape 2 — Stack applicative..."
cd "$PROJECT_DIR"
docker compose up -d \
  mysql redis mlflow api dashboard gateway \
  rabbitmq auth-service \
  redis-commander

echo "⏳ Attente services (15s)..."
sleep 15

# ── Étape 3 : Channels + Chaincodes ──────────
echo ">>> Étape 3 — Channels + Chaincodes..."
source "$PROJECT_DIR/blockchain/fabric-env.sh"

cd "$PROJECT_DIR/blockchain"
make join-channels
make deploy
make init-ledger

# ── Résumé ────────────────────────────────────
echo ""
echo "============================================"
echo "  ✅ BlockML-Gov 100% opérationnel !"
echo "============================================"
echo "  🖥️  Dashboard  : http://localhost:8501"
echo "  📡 API Docs   : http://localhost:8000/docs"
echo "  🔬 MLflow     : http://localhost:5000"
echo "  🔗 Gateway    : http://localhost:9999/health"
echo "  📊 Redis UI   : http://localhost:8081"
echo "  🐇 RabbitMQ   : http://localhost:15672  (guest/guest)"
echo "  💾 CouchDB    : http://localhost:5984/_utils"
echo "  📨 Kafka UI   : http://localhost:8080"
echo "============================================"
echo ""
echo "  Pour démarrer le streaming Kafka :"
echo "  cd $PROJECT_DIR"
echo "  docker compose up -d zookeeper kafka kafka-ui transaction-producer fraud-consumer"
echo "============================================"
