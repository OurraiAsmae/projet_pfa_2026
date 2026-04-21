package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

var (
	cryptoPath = getEnv("CRYPTO_PATH", "/crypto-material")
	fabricCfg  = getEnv("FABRIC_CFG_PATH", "/fabric-config")
	peerBin    = getEnv("PEER_BIN", "/fabric-bin/peer")
)

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

type DecisionRequest struct {
	TxID     string  `json:"tx_id"`
	Zone     string  `json:"zone"`
	ShapHash string  `json:"shap_hash"`
	ModelID  string  `json:"model_id"`
	CardID   string  `json:"card_id"`
	ClientID string  `json:"client_id"`
	Score    float64 `json:"score"`
}

type APIResponse struct {
	Success bool   `json:"success"`
	ID      string `json:"id"`
	Message string `json:"message"`
}

func peerInvoke(channel, chaincode, fcn string, args []string, mspUser string) (string, error) {
	argsJSON := `{"function":"` + fcn + `","Args":[`
	for i, a := range args {
		if i > 0 {
			argsJSON += ","
		}
		argsJSON += `"` + a + `"`
	}
	argsJSON += `]}`

	peerArgs := []string{
		"chaincode", "invoke",
		"-o", "orderer.fraud-governance.com:7050",
		"-C", channel,
		"-n", chaincode,
		"--tls",
		"--cafile", filepath.Join(cryptoPath,
			"ordererOrganizations/fraud-governance.com/orderers/orderer.fraud-governance.com/tls/ca.crt"),
		"--peerAddresses", "peer0.bank.fraud-governance.com:7051",
		"--tlsRootCertFiles", filepath.Join(cryptoPath,
			"peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt"),
		"-c", argsJSON,
	}

	env := append(os.Environ(),
		"FABRIC_CFG_PATH="+fabricCfg,
		"CORE_PEER_TLS_ENABLED=true",
		"CORE_PEER_LOCALMSPID=BankMSP",
		"CORE_PEER_MSPCONFIGPATH="+filepath.Join(cryptoPath,
			"peerOrganizations/bank.fraud-governance.com/users/"+mspUser+"/msp"),
		"CORE_PEER_ADDRESS=peer0.bank.fraud-governance.com:7051",
		"CORE_PEER_TLS_ROOTCERT_FILE="+filepath.Join(cryptoPath,
			"peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt"),
	)

	cmd := exec.Command(peerBin, peerArgs...)
	cmd.Env = env
	out, err := cmd.CombinedOutput()
	return string(out), err
}

func recordDecisionHandler(w http.ResponseWriter, r *http.Request) {
	var req DecisionRequest
	json.NewDecoder(r.Body).Decode(&req)

	score := fmt.Sprintf("%.4f", req.Score)
	cardID := req.CardID
	if cardID == "" {
		cardID = "CARD-" + req.TxID
	}
	clientID := req.ClientID
	if clientID == "" {
		clientID = "CLIENT-DEFAULT"
	}

	out, err := peerInvoke(
		"frauddetection", "fraud-detection-cc", "RecordDecision",
		[]string{req.TxID, req.Zone, req.ShapHash, req.ModelID, cardID, clientID, score},
		"Admin@bank.fraud-governance.com",
	)

	resp := APIResponse{ID: req.TxID}
	if err != nil {
		resp.Success = false
		resp.Message = out
		log.Printf("ERREUR RecordDecision %s: %s", req.TxID, out)
	} else {
		resp.Success = true
		resp.Message = "Enregistre sur blockchain"
		log.Printf("OK RecordDecision %s zone=%s", req.TxID, req.Zone)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func submitModelHandler(w http.ResponseWriter, r *http.Request) {
	var req map[string]string
	json.NewDecoder(r.Body).Decode(&req)

	out, err := peerInvoke(
		"modelgovernance", "model-governance-cc", "SubmitModel",
		[]string{req["model_id"], req["version"], req["data_hash"],
			req["mlflow_run_id"], req["model_card_cid"],
			req["auc"], req["f1"], req["precision"], req["recall"]},
		"User1@bank.fraud-governance.com",
	)

	resp := APIResponse{ID: req["model_id"]}
	if err != nil {
		if strings.Contains(out, "existe deja") {
			resp.Success = true
			resp.Message = "Modele deja enregistre"
		} else {
			resp.Success = false
			resp.Message = out
		}
	} else {
		resp.Success = true
		resp.Message = "Modele soumis sur blockchain"
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func recordDriftHandler(w http.ResponseWriter, r *http.Request) {
	var req map[string]string
	json.NewDecoder(r.Body).Decode(&req)

	out, err := peerInvoke(
		"modelgovernance", "model-governance-cc", "RecordDrift",
		[]string{
			req["model_id"], req["drift_score"], req["affected_features"],
			req["severity"], req["auc_degradation"], req["recommendation"],
		},
		"User3@bank.fraud-governance.com",
	)

	resp := APIResponse{ID: req["model_id"]}
	if err != nil {
		resp.Success = false
		resp.Message = out
	} else {
		resp.Success = true
		resp.Message = "Drift enregistre sur blockchain"
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func validateComplianceHandler(w http.ResponseWriter, r *http.Request) {
	var req map[string]string
	json.NewDecoder(r.Body).Decode(&req)
	out, err := peerInvoke(
		"modelgovernance", "model-governance-cc", "ValidateCompliance",
		[]string{req["model_id"], "User2@bank.fraud-governance.com"},
		"User2@bank.fraud-governance.com",
	)
	resp := APIResponse{ID: req["model_id"]}
	if err != nil {
		resp.Success = false
		resp.Message = out
	} else {
		resp.Success = true
		resp.Message = "Conformite validee sur blockchain"
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func approveTechnicalHandler(w http.ResponseWriter, r *http.Request) {
	var req map[string]string
	json.NewDecoder(r.Body).Decode(&req)
	out, err := peerInvoke(
		"modelgovernance", "model-governance-cc", "ApproveTechnical",
		[]string{req["model_id"], "User3@bank.fraud-governance.com"},
		"User3@bank.fraud-governance.com",
	)
	resp := APIResponse{ID: req["model_id"]}
	if err != nil {
		resp.Success = false
		resp.Message = out
	} else {
		resp.Success = true
		resp.Message = "Approuve techniquement sur blockchain"
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func deployModelHandler(w http.ResponseWriter, r *http.Request) {
	var req map[string]string
	json.NewDecoder(r.Body).Decode(&req)
	out, err := peerInvoke(
		"modelgovernance", "model-governance-cc", "Deploy",
		[]string{req["model_id"], req["admin_id"]},
		"Admin@bank.fraud-governance.com",
	)
	resp := APIResponse{ID: req["model_id"]}
	if err != nil {
		resp.Success = false
		resp.Message = out
	} else {
		resp.Success = true
		resp.Message = "Modele deploye en production sur blockchain"
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func revokeModelHandler(w http.ResponseWriter, r *http.Request) {
	var req map[string]string
	json.NewDecoder(r.Body).Decode(&req)
	out, err := peerInvoke(
		"modelgovernance", "model-governance-cc", "RevokeModel",
		[]string{req["model_id"], req["reason"]},
		"Admin@bank.fraud-governance.com",
	)
	resp := APIResponse{ID: req["model_id"]}
	if err != nil {
		resp.Success = false
		resp.Message = out
	} else {
		resp.Success = true
		resp.Message = "Modele revoque sur blockchain"
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func getModelHandler(w http.ResponseWriter, r *http.Request) {
	modelID := strings.TrimPrefix(r.URL.Path, "/model/")
	peerArgs := []string{
		"chaincode", "query",
		"-C", "modelgovernance",
		"-n", "model-governance-cc",
		"-c", `{"function":"GetModel","Args":["` + modelID + `"]}`,
	}
	env := append(os.Environ(),
		"FABRIC_CFG_PATH="+fabricCfg,
		"CORE_PEER_TLS_ENABLED=true",
		"CORE_PEER_LOCALMSPID=BankMSP",
		"CORE_PEER_MSPCONFIGPATH="+filepath.Join(cryptoPath,
			"peerOrganizations/bank.fraud-governance.com/users/User1@bank.fraud-governance.com/msp"),
		"CORE_PEER_ADDRESS=peer0.bank.fraud-governance.com:7051",
		"CORE_PEER_TLS_ROOTCERT_FILE="+filepath.Join(cryptoPath,
			"peerOrganizations/bank.fraud-governance.com/peers/peer0.bank.fraud-governance.com/tls/ca.crt"),
	)
	cmd := exec.Command(peerBin, peerArgs...)
	cmd.Env = env
	out, err := cmd.CombinedOutput()
	w.Header().Set("Content-Type", "application/json")
	if err != nil {
		json.NewEncoder(w).Encode(map[string]string{"error": string(out)})
	} else {
		w.Write(out)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":    "ok",
		"timestamp": time.Now().Format(time.RFC3339),
		"peer":      "peer0.bank.fraud-governance.com:7051",
	})
}

func main() {
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/record-decision", recordDecisionHandler)
	http.HandleFunc("/submit-model", submitModelHandler)
	http.HandleFunc("/record-drift", recordDriftHandler)
	http.HandleFunc("/validate-compliance", validateComplianceHandler)
	http.HandleFunc("/approve-technical", approveTechnicalHandler)
	http.HandleFunc("/deploy-model", deployModelHandler)
	http.HandleFunc("/revoke-model", revokeModelHandler)
	http.HandleFunc("/model/", getModelHandler)

	port := getEnv("PORT", "9999")
	log.Printf("Gateway port %s | crypto=%s | cfg=%s | peer=%s",
		port, cryptoPath, fabricCfg, peerBin)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
