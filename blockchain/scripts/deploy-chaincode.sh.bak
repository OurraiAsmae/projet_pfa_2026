#!/bin/bash
set -e

CC_NAME=$1
CHANNEL=$2
SEQ=$3

FABRIC_BIN=~/fraud-governance-system/fabric-samples/bin
CC_DIR=~/fraud-governance-system/blockchain/chaincodes/$CC_NAME

source ~/fabric-env.sh

echo ">>> Packaging $CC_NAME..."
cd $CC_DIR
$FABRIC_BIN/peer lifecycle chaincode package /tmp/${CC_NAME}-${CHANNEL}-${SEQ}.tar.gz \
    --path . --lang golang --label ${CC_NAME}_${SEQ}

echo ">>> Install sur Bank..."
CORE_PEER_TLS_ENABLED=true \
CORE_PEER_LOCALMSPID="BankMSP" \
CORE_PEER_MSPCONFIGPATH="$BANK_ADMIN" \
CORE_PEER_ADDRESS="$BANK_PEER" \
CORE_PEER_TLS_ROOTCERT_FILE="$BANK_TLS" \
$FABRIC_BIN/peer lifecycle chaincode install /tmp/${CC_NAME}-${CHANNEL}-${SEQ}.tar.gz 2>&1 | tail -2

if [ "$CHANNEL" = "compliance" ] || [ "$CHANNEL" = "regulatory" ]; then
    echo ">>> Install sur Audit..."
    CORE_PEER_TLS_ENABLED=true \
    CORE_PEER_LOCALMSPID="AuditMSP" \
    CORE_PEER_MSPCONFIGPATH="$AUDIT_ADMIN" \
    CORE_PEER_ADDRESS="$AUDIT_PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$AUDIT_TLS" \
    $FABRIC_BIN/peer lifecycle chaincode install /tmp/${CC_NAME}-${CHANNEL}-${SEQ}.tar.gz 2>&1 | tail -2
fi

if [ "$CHANNEL" = "regulatory" ]; then
    echo ">>> Install sur Regulator..."
    CORE_PEER_TLS_ENABLED=true \
    CORE_PEER_LOCALMSPID="RegulatorMSP" \
    CORE_PEER_MSPCONFIGPATH="$REGULATOR_ADMIN" \
    CORE_PEER_ADDRESS="$REGULATOR_PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$REGULATOR_TLS" \
    $FABRIC_BIN/peer lifecycle chaincode install /tmp/${CC_NAME}-${CHANNEL}-${SEQ}.tar.gz 2>&1 | tail -2
fi

echo ">>> Récupération Package ID..."
PKG_ID=$(CORE_PEER_TLS_ENABLED=true \
CORE_PEER_LOCALMSPID="BankMSP" \
CORE_PEER_MSPCONFIGPATH="$BANK_ADMIN" \
CORE_PEER_ADDRESS="$BANK_PEER" \
CORE_PEER_TLS_ROOTCERT_FILE="$BANK_TLS" \
$FABRIC_BIN/peer lifecycle chaincode queryinstalled 2>&1 \
| grep "${CC_NAME}_${SEQ}" | head -1 \
| awk -F'Package ID: ' '{print $2}' | awk -F',' '{print $1}')
echo "Package ID: $PKG_ID"

# Définir la signature policy selon le channel
if [ "$CHANNEL" = "modelgovernance" ] || [ "$CHANNEL" = "frauddetection" ]; then
    POLICY="OR('BankMSP.peer')"
elif [ "$CHANNEL" = "compliance" ]; then
    POLICY="OR('BankMSP.peer','AuditMSP.peer')"
else
    POLICY="OR('AuditMSP.peer','RegulatorMSP.peer')"
fi

echo ">>> Approve Bank (policy: $POLICY)..."
CORE_PEER_TLS_ENABLED=true \
CORE_PEER_LOCALMSPID="BankMSP" \
CORE_PEER_MSPCONFIGPATH="$BANK_ADMIN" \
CORE_PEER_ADDRESS="$BANK_PEER" \
CORE_PEER_TLS_ROOTCERT_FILE="$BANK_TLS" \
$FABRIC_BIN/peer lifecycle chaincode approveformyorg \
    -o $ORDERER_ADDRESS --tls --cafile $ORDERER_CA \
    --channelID $CHANNEL --name $CC_NAME \
    --version $SEQ --sequence $SEQ \
    --signature-policy "$POLICY" \
    --package-id $PKG_ID 2>&1 | tail -2

if [ "$CHANNEL" = "compliance" ] || [ "$CHANNEL" = "regulatory" ]; then
    echo ">>> Approve Audit..."
    CORE_PEER_TLS_ENABLED=true \
    CORE_PEER_LOCALMSPID="AuditMSP" \
    CORE_PEER_MSPCONFIGPATH="$AUDIT_ADMIN" \
    CORE_PEER_ADDRESS="$AUDIT_PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$AUDIT_TLS" \
    $FABRIC_BIN/peer lifecycle chaincode approveformyorg \
        -o $ORDERER_ADDRESS --tls --cafile $ORDERER_CA \
        --channelID $CHANNEL --name $CC_NAME \
        --version $SEQ --sequence $SEQ \
        --signature-policy "$POLICY" \
        --package-id $PKG_ID 2>&1 | tail -2
fi

if [ "$CHANNEL" = "regulatory" ]; then
    echo ">>> Approve Regulator..."
    CORE_PEER_TLS_ENABLED=true \
    CORE_PEER_LOCALMSPID="RegulatorMSP" \
    CORE_PEER_MSPCONFIGPATH="$REGULATOR_ADMIN" \
    CORE_PEER_ADDRESS="$REGULATOR_PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$REGULATOR_TLS" \
    $FABRIC_BIN/peer lifecycle chaincode approveformyorg \
        -o $ORDERER_ADDRESS --tls --cafile $ORDERER_CA \
        --channelID $CHANNEL --name $CC_NAME \
        --version $SEQ --sequence $SEQ \
        --signature-policy "$POLICY" \
        --package-id $PKG_ID 2>&1 | tail -2
fi

echo ">>> Commit sur $CHANNEL..."
PEER_ARGS="--peerAddresses $BANK_PEER --tlsRootCertFiles $BANK_TLS"
if [ "$CHANNEL" = "compliance" ]; then
    PEER_ARGS="$PEER_ARGS --peerAddresses $AUDIT_PEER --tlsRootCertFiles $AUDIT_TLS"
fi
if [ "$CHANNEL" = "regulatory" ]; then
    PEER_ARGS="--peerAddresses $AUDIT_PEER --tlsRootCertFiles $AUDIT_TLS --peerAddresses $REGULATOR_PEER --tlsRootCertFiles $REGULATOR_TLS"
fi

CORE_PEER_TLS_ENABLED=true \
CORE_PEER_LOCALMSPID="BankMSP" \
CORE_PEER_MSPCONFIGPATH="$BANK_ADMIN" \
CORE_PEER_ADDRESS="$BANK_PEER" \
CORE_PEER_TLS_ROOTCERT_FILE="$BANK_TLS" \
$FABRIC_BIN/peer lifecycle chaincode commit \
    -o $ORDERER_ADDRESS --tls --cafile $ORDERER_CA \
    --channelID $CHANNEL --name $CC_NAME \
    --version $SEQ --sequence $SEQ \
    --signature-policy "$POLICY" \
    $PEER_ARGS 2>&1 | tail -3

echo "✅ $CC_NAME déployé sur $CHANNEL séquence $SEQ"
