#!/bin/bash
source ~/fabric-env.sh

ORDERER_TLS_DIR=~/fraud-governance-system/blockchain/network/crypto-material/ordererOrganizations/fraud-governance.com/orderers/orderer.fraud-governance.com/tls
BLOCKS=~/fraud-governance-system/blockchain/network/channel-artifacts
FABRIC_BIN=~/fraud-governance-system/fabric-samples/bin

echo ">>> Création channels sur orderer..."
for CHANNEL in modelgovernance frauddetection compliance regulatory; do
    osnadmin channel join \
        --channelID $CHANNEL \
        --config-block $BLOCKS/${CHANNEL}.block \
        -o orderer.fraud-governance.com:7053 \
        --ca-file $ORDERER_TLS_DIR/ca.crt \
        --client-cert $ORDERER_TLS_DIR/server.crt \
        --client-key $ORDERER_TLS_DIR/server.key 2>/dev/null || true
    echo "✅ $CHANNEL"
done

sleep 3

echo ">>> Bank rejoint les channels..."
for CHANNEL in modelgovernance frauddetection compliance; do
    CORE_PEER_TLS_ENABLED=true CORE_PEER_LOCALMSPID="BankMSP" \
    CORE_PEER_MSPCONFIGPATH="$BANK_ADMIN" CORE_PEER_ADDRESS="$BANK_PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$BANK_TLS" \
    $FABRIC_BIN/peer channel join -b $BLOCKS/${CHANNEL}.block 2>&1 | tail -1
    echo "✅ bank → $CHANNEL"
done

echo ">>> Audit rejoint les channels..."
for CHANNEL in compliance regulatory; do
    CORE_PEER_TLS_ENABLED=true CORE_PEER_LOCALMSPID="AuditMSP" \
    CORE_PEER_MSPCONFIGPATH="$AUDIT_ADMIN" CORE_PEER_ADDRESS="$AUDIT_PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$AUDIT_TLS" \
    $FABRIC_BIN/peer channel join -b $BLOCKS/${CHANNEL}.block 2>&1 | tail -1
    echo "✅ audit → $CHANNEL"
done

echo ">>> Regulator rejoint regulatory..."
CORE_PEER_TLS_ENABLED=true CORE_PEER_LOCALMSPID="RegulatorMSP" \
CORE_PEER_MSPCONFIGPATH="$REGULATOR_ADMIN" CORE_PEER_ADDRESS="$REGULATOR_PEER" \
CORE_PEER_TLS_ROOTCERT_FILE="$REGULATOR_TLS" \
$FABRIC_BIN/peer channel join -b $BLOCKS/regulatory.block 2>&1 | tail -1
echo "✅ regulator → regulatory"

echo "✅ Tous les channels rejoints"
