SHELL := /bin/bash
FABRIC_BIN := $(HOME)/fraud-governance-system/fabric-samples/bin
NETWORK_DIR := $(HOME)/fraud-governance-system/blockchain/network
CC_DIR := $(HOME)/fraud-governance-system/blockchain/chaincodes
SCRIPTS_DIR := $(HOME)/fraud-governance-system/blockchain/scripts

MGCC_SEQ := 2
FDCC_SEQ := 1
CCC_SEQ  := 1

.PHONY: help compile deploy deploy-mgcc deploy-fdcc deploy-ccc init-ledger verify verify-channels verify-chaincodes join-channels test clean status logs

help:
	@echo "make compile / deploy / init-ledger / verify / test / status"

compile:
	@cd $(CC_DIR)/model-governance-cc && go build ./... && echo "✅ mgcc"
	@cd $(CC_DIR)/fraud-detection-cc && go build ./... && echo "✅ fdcc"
	@cd $(CC_DIR)/compliance-cc && go build ./... && echo "✅ ccc"

deploy: deploy-mgcc deploy-fdcc deploy-ccc
	@echo "✅ Les 3 chaincodes déployés"

deploy-mgcc:
	@source $(HOME)/fabric-env.sh && \
	bash $(SCRIPTS_DIR)/deploy-chaincode.sh model-governance-cc modelgovernance $(MGCC_SEQ)

deploy-fdcc:
	@source $(HOME)/fabric-env.sh && \
	bash $(SCRIPTS_DIR)/deploy-chaincode.sh fraud-detection-cc frauddetection $(FDCC_SEQ)

deploy-ccc:
	@source $(HOME)/fabric-env.sh && \
	bash $(SCRIPTS_DIR)/deploy-chaincode.sh compliance-cc compliance $(CCC_SEQ)
	@source $(HOME)/fabric-env.sh && \
	bash $(SCRIPTS_DIR)/deploy-chaincode.sh compliance-cc regulatory $(CCC_SEQ)

init-ledger:
	@source $(HOME)/fabric-env.sh && \
	CORE_PEER_TLS_ENABLED=true \
	CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" \
	CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" \
	$(FABRIC_BIN)/peer chaincode invoke \
	  -o orderer.fraud-governance.com:7050 --tls --cafile "$$ORDERER_CA" \
	  -C modelgovernance -n model-governance-cc \
	  -c '{"function":"InitLedger","Args":[]}' && echo "✅ mgcc initialisé"
	@sleep 2
	@source $(HOME)/fabric-env.sh && \
	CORE_PEER_TLS_ENABLED=true \
	CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" \
	CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" \
	$(FABRIC_BIN)/peer chaincode invoke \
	  -o orderer.fraud-governance.com:7050 --tls --cafile "$$ORDERER_CA" \
	  -C frauddetection -n fraud-detection-cc \
	  -c '{"function":"InitLedger","Args":[]}' && echo "✅ fdcc initialisé"
	@sleep 2
	@source $(HOME)/fabric-env.sh && \
	CORE_PEER_TLS_ENABLED=true \
	CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" \
	CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" \
	$(FABRIC_BIN)/peer chaincode invoke \
	  -o orderer.fraud-governance.com:7050 --tls --cafile "$$ORDERER_CA" \
	  -C compliance -n compliance-cc \
	  --peerAddresses "$$BANK_PEER" --tlsRootCertFiles "$$BANK_TLS" \
	  --peerAddresses "$$AUDIT_PEER" --tlsRootCertFiles "$$AUDIT_TLS" \
	  -c '{"function":"InitLedger","Args":[]}' && echo "✅ ccc initialisé"
	@echo "✅ Tous les ledgers initialisés"

verify: verify-channels verify-chaincodes

verify-channels:
	@echo "=== Bank ===" && source $(HOME)/fabric-env.sh && \
	CORE_PEER_TLS_ENABLED=true CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" $(FABRIC_BIN)/peer channel list
	@echo "=== Regulator ===" && source $(HOME)/fabric-env.sh && \
	CORE_PEER_TLS_ENABLED=true CORE_PEER_LOCALMSPID="RegulatorMSP" \
	CORE_PEER_MSPCONFIGPATH="$$REGULATOR_ADMIN" CORE_PEER_ADDRESS="$$REGULATOR_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$REGULATOR_TLS" $(FABRIC_BIN)/peer channel list

verify-chaincodes:
	@source $(HOME)/fabric-env.sh && \
	CORE_PEER_TLS_ENABLED=true CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" \
	$(FABRIC_BIN)/peer lifecycle chaincode querycommitted --channelID modelgovernance && \
	$(FABRIC_BIN)/peer lifecycle chaincode querycommitted --channelID frauddetection && \
	$(FABRIC_BIN)/peer lifecycle chaincode querycommitted --channelID compliance

join-channels:
	@bash $(SCRIPTS_DIR)/join-channels.sh

status:
	@docker ps --format "table {{.Names}}\t{{.Status}}"

logs:
	@docker logs network-orderer.fraud-governance.com-1 2>&1 | tail -5
	@docker logs network-peer0.bank.fraud-governance.com-1 2>&1 | tail -5

clean:
	@rm -f /tmp/mgcc-*.tar.gz /tmp/fdcc-*.tar.gz /tmp/ccc-*.tar.gz
	@echo "✅ Nettoyé"

verify-chaincodes:
	@source $(HOME)/fabric-env.sh && \
	CORE_PEER_TLS_ENABLED=true \
	CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" \
	CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" \
	$(FABRIC_BIN)/peer lifecycle chaincode querycommitted --channelID modelgovernance && \
	CORE_PEER_TLS_ENABLED=true \
	CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" \
	CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" \
	$(FABRIC_BIN)/peer lifecycle chaincode querycommitted --channelID frauddetection && \
	CORE_PEER_TLS_ENABLED=true \
	CORE_PEER_LOCALMSPID="BankMSP" \
	CORE_PEER_MSPCONFIGPATH="$$BANK_ADMIN" \
	CORE_PEER_ADDRESS="$$BANK_PEER" \
	CORE_PEER_TLS_ROOTCERT_FILE="$$BANK_TLS" \
	$(FABRIC_BIN)/peer lifecycle chaincode querycommitted --channelID compliance
	@echo "✅ Chaincodes vérifiés"
