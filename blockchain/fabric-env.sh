# Détection dynamique du dossier racine du projet
if [ -n "$BASH_SOURCE" ]; then
    DIR_OF_ENV="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
else
    DIR_OF_ENV="$( cd "$( dirname "$0" )" && pwd )"
fi
export PROJECT_ROOT="$( cd "$DIR_OF_ENV/.." && pwd )"

export FABRIC_CFG_PATH="$PROJECT_ROOT/blockchain/network"
export CRYPTO="$PROJECT_ROOT/blockchain/network/crypto-material"
export ORDERER_CA=$CRYPTO/ordererOrganizations/fraud-governance.com/tlsca/tlsca.fraud-governance.com-cert.pem
export ORDERER_ADDRESS=orderer.fraud-governance.com:7050
export BANK_ADMIN=$CRYPTO/peerOrganizations/bank.fraud-governance.com/users/Admin@bank.fraud-governance.com/msp
export BANK_PEER=peer0.bank.fraud-governance.com:7051
export BANK_TLS=$CRYPTO/peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt
export AUDIT_ADMIN=$CRYPTO/peerOrganizations/audit.fraud-governance.com/users/Admin@audit.fraud-governance.com/msp
export AUDIT_PEER=peer0.audit.fraud-governance.com:9051
export AUDIT_TLS=$CRYPTO/peerOrganizations/audit.fraud-governance.com/peers/peer0.audit.fraud-governance.com/tls/ca.crt
export REGULATOR_ADMIN=$CRYPTO/peerOrganizations/regulator.fraud-governance.com/users/Admin@regulator.fraud-governance.com/msp
export REGULATOR_PEER=peer0.regulator.fraud-governance.com:10051
export REGULATOR_TLS=$CRYPTO/peerOrganizations/regulator.fraud-governance.com/peers/peer0.regulator.fraud-governance.com/tls/ca.crt
