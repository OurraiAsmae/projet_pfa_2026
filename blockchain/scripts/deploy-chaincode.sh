#!/bin/bash
set -e

CC_NAME=$1
CHANNEL=$2
SEQ=$3

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../fabric-env.sh"

FABRIC_BIN="$PROJECT_ROOT/fabric-samples/bin"
CC_DIR="$PROJECT_ROOT/blockchain/chaincodes/$CC_NAME"

get_org_vars() {
    case $1 in
        bank)      MSPID="BankMSP";      ADMIN="$BANK_ADMIN";      PEER="$BANK_PEER";      TLS="$BANK_TLS" ;;
        audit)     MSPID="AuditMSP";     ADMIN="$AUDIT_ADMIN";     PEER="$AUDIT_PEER";     TLS="$AUDIT_TLS" ;;
        regulator) MSPID="RegulatorMSP"; ADMIN="$REGULATOR_ADMIN"; PEER="$REGULATOR_PEER"; TLS="$REGULATOR_TLS" ;;
    esac
}

if [ "$CHANNEL" = "modelgovernance" ] || [ "$CHANNEL" = "frauddetection" ]; then
    ORGS="bank"
    POLICY="OR('BankMSP.peer')"
elif [ "$CHANNEL" = "compliance" ]; then
    ORGS="bank audit"
    POLICY="OR('BankMSP.peer','AuditMSP.peer')"
elif [ "$CHANNEL" = "regulatory" ]; then
    ORGS="audit regulator"
    POLICY="OR('AuditMSP.peer','RegulatorMSP.peer')"
fi

SUBMIT_ORG=$(echo $ORGS | awk '{print $1}')

echo ">>> Packaging $CC_NAME..."
cd $CC_DIR
$FABRIC_BIN/peer lifecycle chaincode package /tmp/${CC_NAME}-${CHANNEL}-${SEQ}.tar.gz \
    --path . --lang golang --label ${CC_NAME}_${SEQ}

for ORG in $ORGS; do
    get_org_vars $ORG
    echo ">>> Install sur $ORG..."
    CORE_PEER_TLS_ENABLED=true \
    CORE_PEER_LOCALMSPID="$MSPID" \
    CORE_PEER_MSPCONFIGPATH="$ADMIN" \
    CORE_PEER_ADDRESS="$PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$TLS" \
    $FABRIC_BIN/peer lifecycle chaincode install /tmp/${CC_NAME}-${CHANNEL}-${SEQ}.tar.gz 2>&1 | tail -2 || true
done

get_org_vars $SUBMIT_ORG
echo ">>> Récupération Package ID..."
PKG_ID=$(CORE_PEER_TLS_ENABLED=true \
CORE_PEER_LOCALMSPID="$MSPID" \
CORE_PEER_MSPCONFIGPATH="$ADMIN" \
CORE_PEER_ADDRESS="$PEER" \
CORE_PEER_TLS_ROOTCERT_FILE="$TLS" \
$FABRIC_BIN/peer lifecycle chaincode queryinstalled 2>&1 \
| grep "${CC_NAME}_${SEQ}" | head -1 \
| awk -F'Package ID: ' '{print $2}' | awk -F',' '{print $1}')
echo "Package ID: $PKG_ID"

for ORG in $ORGS; do
    get_org_vars $ORG
    echo ">>> Approve $ORG (policy: $POLICY)..."
    CORE_PEER_TLS_ENABLED=true \
    CORE_PEER_LOCALMSPID="$MSPID" \
    CORE_PEER_MSPCONFIGPATH="$ADMIN" \
    CORE_PEER_ADDRESS="$PEER" \
    CORE_PEER_TLS_ROOTCERT_FILE="$TLS" \
    $FABRIC_BIN/peer lifecycle chaincode approveformyorg \
        -o $ORDERER_ADDRESS --tls --cafile $ORDERER_CA \
        --channelID $CHANNEL --name $CC_NAME \
        --version $SEQ --sequence $SEQ \
        --signature-policy "$POLICY" \
        --package-id $PKG_ID 2>&1 | tail -2
done

PEER_ARGS=""
for ORG in $ORGS; do
    get_org_vars $ORG
    PEER_ARGS="$PEER_ARGS --peerAddresses $PEER --tlsRootCertFiles $TLS"
done

get_org_vars $SUBMIT_ORG
echo ">>> Commit sur $CHANNEL..."
CORE_PEER_TLS_ENABLED=true \
CORE_PEER_LOCALMSPID="$MSPID" \
CORE_PEER_MSPCONFIGPATH="$ADMIN" \
CORE_PEER_ADDRESS="$PEER" \
CORE_PEER_TLS_ROOTCERT_FILE="$TLS" \
$FABRIC_BIN/peer lifecycle chaincode commit \
    -o $ORDERER_ADDRESS --tls --cafile $ORDERER_CA \
    --channelID $CHANNEL --name $CC_NAME \
    --version $SEQ --sequence $SEQ \
    --signature-policy "$POLICY" \
    $PEER_ARGS 2>&1 | tail -3

echo "✅ $CC_NAME déployé sur $CHANNEL séquence $SEQ"
