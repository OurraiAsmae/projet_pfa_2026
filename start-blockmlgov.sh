#!/bin/bash
echo "============================================"
echo "  🚀 BlockML-Gov — Démarrage complet"
echo "============================================"

# 1. Réseau Hyperledger Fabric
echo ">>> Étape 1 — Réseau Hyperledger Fabric..."
cd ~/fraud-governance-system/blockchain/network
docker compose -f docker-compose-fabric.yml up -d
echo "⏳ Attente Fabric (20s)..."
sleep 20

# 2. Stack applicative complète
echo ">>> Étape 2 — Stack applicative..."
cd ~/fraud-governance-system
docker compose up -d \
  redis mlflow api dashboard gateway \
  rabbitmq auth-service \
  redis-commander

echo "⏳ Attente services (15s)..."
sleep 15

# 3. Channels + Chaincodes
echo ">>> Étape 3 — Channels + Chaincodes..."
cd ~/fraud-governance-system/blockchain
make join-channels
make deploy
make init-ledger

# 4. /etc/hosts
echo ">>> Étape 4 — /etc/hosts..."
sudo sed -i '/fraud-governance/d' /etc/hosts
sudo bash -c 'cat >> /etc/hosts << HOSTS
127.0.0.1  orderer.fraud-governance.com
127.0.0.1  peer0.bank.fraud-governance.com
127.0.0.1  peer0.audit.fraud-governance.com
127.0.0.1  peer0.regulator.fraud-governance.com
HOSTS'

echo ""
echo "============================================"
echo "  ✅ BlockML-Gov 100% opérationnel !"
echo "============================================"
echo "  Dashboard  : http://localhost:8501"
echo "  API Docs   : http://localhost:8000/docs"
echo "  MLflow     : http://localhost:5000"
echo "  Gateway    : http://localhost:9999/health"
echo "  Redis UI   : http://localhost:8081"
echo "  RabbitMQ   : http://localhost:15672"
echo "  CouchDB    : http://localhost:5984/_utils"
echo "  Kafka UI   : http://localhost:8080"
echo "============================================"
echo ""
echo "  Pour démarrer Kafka streaming:"
echo "  cd ~/fraud-governance-system"
echo "  docker compose up -d zookeeper kafka kafka-ui transaction-producer fraud-consumer"
echo "============================================"
