package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type ProductionPeriod struct {
	StartDate string `json:"startDate"`
	EndDate   string `json:"endDate"`
	Reason    string `json:"reason"`
	Duration  string `json:"duration"`
}

type ModelAsset struct {
	ModelID             string             `json:"modelID"`
	Version             string             `json:"version"`
	DataHash            string             `json:"dataHash"`
	MLflowRunID         string             `json:"mlflowRunID"`
	AUC                 float64            `json:"auc"`
	F1                  float64            `json:"f1"`
	Precision           float64            `json:"precision"`
	Recall              float64            `json:"recall"`
	ModelCardCID        string             `json:"modelCardCID"`
	ScientistID         string             `json:"scientistID"`
	ComplianceOfficerID string             `json:"complianceOfficerID"`
	MLEngineerID        string             `json:"mlEngineerID"`
	Status              string             `json:"status"`
	SubmittedAt         string             `json:"submittedAt"`
	ComplianceAt        string             `json:"complianceAt"`
	TechnicalAt         string             `json:"technicalAt"`
	RevokeReason        string             `json:"revokeReason"`
	QualityScore        float64            `json:"qualityScore"`
	ProductionPeriods   []ProductionPeriod `json:"productionPeriods"`
}

type ThresholdAsset struct {
	AUCMin         float64 `json:"aucMin"`
	F1Min          float64 `json:"f1Min"`
	PrecisionMin   float64 `json:"precisionMin"`
	RecallMin      float64 `json:"recallMin"`
	Justification  string  `json:"justification"`
	ApprovedByC    string  `json:"approvedByCompliance"`
	ApprovedByML   string  `json:"approvedByML"`
	ValidFrom      string  `json:"validFrom"`
	ReviewDeadline string  `json:"reviewDeadline"`
	Status         string  `json:"status"`
}

type CertifiedModelEntry struct {
	ModelID     string  `json:"modelID"`
	AUC         float64 `json:"auc"`
	CertifiedAt string  `json:"certifiedAt"`
}

type CertifiedModelsStack struct {
	Entries []CertifiedModelEntry `json:"entries"`
	MaxSize int                   `json:"maxSize"`
}

type DriftAsset struct {
	DriftID       string `json:"driftID"`
	ModelID       string `json:"modelID"`
	DriftType     string `json:"driftType"`
	Severity      string `json:"severity"`
	MetricsBefore string `json:"metricsBefore"`
	MetricsAfter  string `json:"metricsAfter"`
	DetectedAt    string `json:"detectedAt"`
	Status        string `json:"status"`
	ClosedBy      string `json:"closedBy"`
	ClosedAt      string `json:"closedAt"`
	Justification string `json:"justification"`
}

type ModelGovernanceContract struct {
	contractapi.Contract
}

func getCallerID(ctx contractapi.TransactionContextInterface) (string, error) {
	id, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return "", fmt.Errorf("impossible de lire identite: %v", err)
	}
	decoded, err := base64.StdEncoding.DecodeString(id)
	if err != nil {
		decoded = []byte(id)
	}
	decodedStr := string(decoded)
	parts := strings.Split(decodedStr, "::")
	for _, part := range parts {
		for _, field := range strings.Split(part, ",") {
			field = strings.TrimSpace(field)
			if strings.HasPrefix(field, "CN=") {
				cn := strings.TrimPrefix(field, "CN=")
				if strings.HasPrefix(cn, "User") || strings.HasPrefix(cn, "Admin") {
					return cn, nil
				}
			}
		}
	}
	return decodedStr, nil
}

func getTxTime(ctx contractapi.TransactionContextInterface) string {
	ts, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return time.Now().UTC().Format(time.RFC3339)
	}
	return time.Unix(ts.Seconds, 0).UTC().Format(time.RFC3339)
}

func calculateQualityScore(auc, f1, precision, recall float64) float64 {
	return (auc*0.4 + f1*0.3 + precision*0.15 + recall*0.15) * 100
}

func (c *ModelGovernanceContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	threshold := ThresholdAsset{
		AUCMin: 0.95, F1Min: 0.85, PrecisionMin: 0.85, RecallMin: 0.80,
		Justification: "Seuils initiaux BAM Q1-2024",
		ApprovedByC: "SYSTEM", ApprovedByML: "SYSTEM",
		ValidFrom:      getTxTime(ctx),
		ReviewDeadline: time.Now().AddDate(0, 6, 0).Format(time.RFC3339),
		Status:         "ACTIVE",
	}
	data, _ := json.Marshal(threshold)
	if err := ctx.GetStub().PutState("THRESHOLD_CURRENT", data); err != nil {
		return err
	}
	stack := CertifiedModelsStack{Entries: []CertifiedModelEntry{}, MaxSize: 3}
	stackData, _ := json.Marshal(stack)
	return ctx.GetStub().PutState("CERTIFIED_MODELS_STACK", stackData)
}

func (c *ModelGovernanceContract) SubmitModel(ctx contractapi.TransactionContextInterface, modelID, version, dataHash, mlflowRunID, modelCardCID string, auc, f1, precision, recall float64) error {
	existing, _ := ctx.GetStub().GetState("MODEL_" + modelID)
	if existing != nil {
		return fmt.Errorf("modele %s existe deja", modelID)
	}
	threshData, err := ctx.GetStub().GetState("THRESHOLD_CURRENT")
	if err != nil || threshData == nil {
		return fmt.Errorf("seuils introuvables — InitLedger requis")
	}
	var t ThresholdAsset
	json.Unmarshal(threshData, &t)
	deadline, _ := time.Parse(time.RFC3339, t.ReviewDeadline)
	if time.Now().After(deadline) {
		return fmt.Errorf("REJET seuils expires depuis %s — revision obligatoire", t.ReviewDeadline)
	}
	if auc < t.AUCMin {
		return fmt.Errorf("REJET AUC=%.4f inferieur au seuil=%.4f", auc, t.AUCMin)
	}
	if f1 < t.F1Min {
		return fmt.Errorf("REJET F1=%.4f inferieur au seuil=%.4f", f1, t.F1Min)
	}
	if precision < t.PrecisionMin {
		return fmt.Errorf("REJET Precision=%.4f inferieure au seuil=%.4f", precision, t.PrecisionMin)
	}
	if recall < t.RecallMin {
		return fmt.Errorf("REJET Recall=%.4f inferieur au seuil=%.4f", recall, t.RecallMin)
	}
	if dataHash == "" {
		return fmt.Errorf("REJET dataHash DVC obligatoire")
	}
	if mlflowRunID == "" {
		return fmt.Errorf("REJET mlflowRunID obligatoire")
	}
	if modelCardCID == "" {
		return fmt.Errorf("REJET modelCardCID IPFS obligatoire")
	}
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	model := ModelAsset{
		ModelID: modelID, Version: version, DataHash: dataHash,
		MLflowRunID: mlflowRunID, AUC: auc, F1: f1, Precision: precision, Recall: recall,
		ModelCardCID: modelCardCID, ScientistID: callerID, Status: "SUBMITTED",
		SubmittedAt: getTxTime(ctx), QualityScore: calculateQualityScore(auc, f1, precision, recall),
		ProductionPeriods: []ProductionPeriod{},
	}
	data, _ := json.Marshal(model)
	ctx.GetStub().PutState("MODEL_"+modelID, data)
	ctx.GetStub().SetEvent("MODEL_SUBMITTED", data)
	return nil
}

func (c *ModelGovernanceContract) ValidateCompliance(ctx contractapi.TransactionContextInterface, modelID string) error {
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User2@bank.fraud-governance.com") {
		return fmt.Errorf("REJET seul User2@bank peut valider conformite signataire: %s", callerID)
	}
	data, _ := ctx.GetStub().GetState("MODEL_" + modelID)
	if data == nil {
		return fmt.Errorf("modele %s introuvable", modelID)
	}
	var model ModelAsset
	json.Unmarshal(data, &model)
	if model.Status != "SUBMITTED" {
		return fmt.Errorf("REJET statut %s invalide pour ValidateCompliance", model.Status)
	}
	model.ComplianceOfficerID = callerID
	model.ComplianceAt = getTxTime(ctx)
	model.Status = "COMPLIANCE_VALIDATED"
	newData, _ := json.Marshal(model)
	ctx.GetStub().PutState("MODEL_"+modelID, newData)
	ctx.GetStub().SetEvent("MODEL_COMPLIANCE_VALIDATED", newData)
	return nil
}

func (c *ModelGovernanceContract) ApproveTechnical(ctx contractapi.TransactionContextInterface, modelID string) error {
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User3@bank.fraud-governance.com") {
		return fmt.Errorf("REJET seul User3@bank peut approuver signataire: %s", callerID)
	}
	data, _ := ctx.GetStub().GetState("MODEL_" + modelID)
	if data == nil {
		return fmt.Errorf("modele %s introuvable", modelID)
	}
	var model ModelAsset
	json.Unmarshal(data, &model)
	if model.Status != "COMPLIANCE_VALIDATED" {
		return fmt.Errorf("REJET statut %s invalide pour ApproveTechnical", model.Status)
	}
	model.MLEngineerID = callerID
	model.TechnicalAt = getTxTime(ctx)
	model.Status = "TECHNICAL_APPROVED"
	newData, _ := json.Marshal(model)
	ctx.GetStub().PutState("MODEL_"+modelID, newData)
	ctx.GetStub().SetEvent("MODEL_TECHNICAL_APPROVED", newData)
	return nil
}

func (c *ModelGovernanceContract) Deploy(ctx contractapi.TransactionContextInterface, modelID string) error {
	data, _ := ctx.GetStub().GetState("MODEL_" + modelID)
	if data == nil {
		return fmt.Errorf("modele %s introuvable", modelID)
	}
	var model ModelAsset
	json.Unmarshal(data, &model)
	if model.Status != "TECHNICAL_APPROVED" {
		return fmt.Errorf("REJET statut %s invalide pour Deploy", model.Status)
	}
	if model.ComplianceOfficerID == model.MLEngineerID {
		return fmt.Errorf("REJET regle quatre yeux violee meme identite: %s", model.ComplianceOfficerID)
	}
	model.ProductionPeriods = append(model.ProductionPeriods, ProductionPeriod{StartDate: getTxTime(ctx), Reason: "deploiement initial"})
	model.Status = "DEPLOYED"
	ctx.GetStub().PutState("MODEL_ACTIVE", []byte(modelID))
	stackData, _ := ctx.GetStub().GetState("CERTIFIED_MODELS_STACK")
	var stack CertifiedModelsStack
	json.Unmarshal(stackData, &stack)
	stack.Entries = append(stack.Entries, CertifiedModelEntry{ModelID: modelID, AUC: model.AUC, CertifiedAt: getTxTime(ctx)})
	if len(stack.Entries) > stack.MaxSize {
		stack.Entries = stack.Entries[len(stack.Entries)-stack.MaxSize:]
	}
	newStackData, _ := json.Marshal(stack)
	ctx.GetStub().PutState("CERTIFIED_MODELS_STACK", newStackData)
	newData, _ := json.Marshal(model)
	ctx.GetStub().PutState("MODEL_"+modelID, newData)
	ctx.GetStub().SetEvent("MODEL_DEPLOYED", newData)
	return nil
}

func (c *ModelGovernanceContract) RevokeModel(ctx contractapi.TransactionContextInterface, modelID, reason string) error {
	data, _ := ctx.GetStub().GetState("MODEL_" + modelID)
	if data == nil {
		return fmt.Errorf("modele %s introuvable", modelID)
	}
	var model ModelAsset
	json.Unmarshal(data, &model)
	if model.Status != "DEPLOYED" {
		return fmt.Errorf("REJET seul DEPLOYED peut etre revoque statut: %s", model.Status)
	}
	now := time.Now()
	for i := len(model.ProductionPeriods) - 1; i >= 0; i-- {
		if model.ProductionPeriods[i].EndDate == "" {
			start, _ := time.Parse(time.RFC3339, model.ProductionPeriods[i].StartDate)
			duration := now.Sub(start)
			model.ProductionPeriods[i].EndDate = now.Format(time.RFC3339)
			model.ProductionPeriods[i].Reason = reason
			model.ProductionPeriods[i].Duration = fmt.Sprintf("%.0f jours", duration.Hours()/24)
			break
		}
	}
	model.Status = "REVOKED"
	model.RevokeReason = reason
	stackData, _ := ctx.GetStub().GetState("CERTIFIED_MODELS_STACK")
	var stack CertifiedModelsStack
	json.Unmarshal(stackData, &stack)
	threshData, _ := ctx.GetStub().GetState("THRESHOLD_CURRENT")
	var thresh ThresholdAsset
	json.Unmarshal(threshData, &thresh)
	fallbackFound := false
	for i := len(stack.Entries) - 1; i >= 0; i-- {
		entry := stack.Entries[i]
		if entry.ModelID == modelID || entry.AUC < thresh.AUCMin {
			continue
		}
		fallbackData, _ := ctx.GetStub().GetState("MODEL_" + entry.ModelID)
		if fallbackData != nil {
			var fallback ModelAsset
			json.Unmarshal(fallbackData, &fallback)
			fallback.ProductionPeriods = append(fallback.ProductionPeriods, ProductionPeriod{StartDate: now.Format(time.RFC3339), Reason: fmt.Sprintf("fallback apres revocation de %s", modelID)})
			fallback.Status = "DEPLOYED"
			newFallbackData, _ := json.Marshal(fallback)
			ctx.GetStub().PutState("MODEL_"+entry.ModelID, newFallbackData)
			ctx.GetStub().PutState("MODEL_ACTIVE", []byte(entry.ModelID))
			fallbackFound = true
			break
		}
	}
	if !fallbackFound {
		ctx.GetStub().DelState("MODEL_ACTIVE")
		ctx.GetStub().SetEvent("NO_FALLBACK_AVAILABLE", []byte(modelID))
	}
	newData, _ := json.Marshal(model)
	ctx.GetStub().PutState("MODEL_"+modelID, newData)
	ctx.GetStub().SetEvent("MODEL_REVOKED", newData)
	return nil
}

func (c *ModelGovernanceContract) RecordDrift(ctx contractapi.TransactionContextInterface, driftID, modelID, driftType, severity, metricsBefore, metricsAfter string) error {
	drift := DriftAsset{DriftID: driftID, ModelID: modelID, DriftType: driftType, Severity: severity, MetricsBefore: metricsBefore, MetricsAfter: metricsAfter, DetectedAt: getTxTime(ctx), Status: "OPEN"}
	data, _ := json.Marshal(drift)
	ctx.GetStub().PutState("DRIFT_"+driftID, data)
	ctx.GetStub().SetEvent("DRIFT_DETECTED", data)
	return nil
}

func (c *ModelGovernanceContract) ConfirmRetrainingAction(ctx contractapi.TransactionContextInterface, driftID, action, justification string) error {
	data, _ := ctx.GetStub().GetState("DRIFT_" + driftID)
	if data == nil {
		return fmt.Errorf("derive %s introuvable", driftID)
	}
	var drift DriftAsset
	json.Unmarshal(data, &drift)
	if drift.Status != "OPEN" {
		return fmt.Errorf("derive %s deja fermee", driftID)
	}
	callerID, _ := getCallerID(ctx)
	drift.Status = "CLOSED"
	drift.ClosedBy = callerID
	drift.ClosedAt = getTxTime(ctx)
	drift.Justification = justification
	newData, _ := json.Marshal(drift)
	ctx.GetStub().PutState("DRIFT_"+driftID, newData)
	ctx.GetStub().SetEvent("DRIFT_CLOSED", newData)
	return nil
}

func (c *ModelGovernanceContract) UpdateThresholds(ctx contractapi.TransactionContextInterface, aucMin, f1Min, precisionMin, recallMin float64, justification, secondSignerID string) error {
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User2@bank.fraud-governance.com") {
		return fmt.Errorf("REJET doit etre Compliance Officer signataire: %s", callerID)
	}
	if !strings.Contains(secondSignerID, "User3@bank.fraud-governance.com") {
		return fmt.Errorf("REJET second signataire doit etre ML Engineer recu: %s", secondSignerID)
	}
	if callerID == secondSignerID {
		return fmt.Errorf("REJET signataires doivent etre distincts")
	}
	oldData, _ := ctx.GetStub().GetState("THRESHOLD_CURRENT")
	if oldData != nil {
		ctx.GetStub().PutState("THRESHOLD_ARCHIVE_"+time.Now().Format("20060102150405"), oldData)
	}
	threshold := ThresholdAsset{
		AUCMin: aucMin, F1Min: f1Min, PrecisionMin: precisionMin, RecallMin: recallMin,
		Justification: justification, ApprovedByC: callerID, ApprovedByML: secondSignerID,
		ValidFrom: getTxTime(ctx), ReviewDeadline: time.Now().AddDate(0, 6, 0).Format(time.RFC3339), Status: "ACTIVE",
	}
	data, _ := json.Marshal(threshold)
	ctx.GetStub().PutState("THRESHOLD_CURRENT", data)
	ctx.GetStub().SetEvent("THRESHOLDS_UPDATED", data)
	return nil
}

func (c *ModelGovernanceContract) GetModel(ctx contractapi.TransactionContextInterface, modelID string) (*ModelAsset, error) {
	data, _ := ctx.GetStub().GetState("MODEL_" + modelID)
	if data == nil {
		return nil, fmt.Errorf("modele %s introuvable", modelID)
	}
	var model ModelAsset
	json.Unmarshal(data, &model)
	return &model, nil
}

func (c *ModelGovernanceContract) GetThresholds(ctx contractapi.TransactionContextInterface) (*ThresholdAsset, error) {
	data, _ := ctx.GetStub().GetState("THRESHOLD_CURRENT")
	if data == nil {
		return nil, fmt.Errorf("aucun seuil defini")
	}
	var threshold ThresholdAsset
	json.Unmarshal(data, &threshold)
	return &threshold, nil
}

func (c *ModelGovernanceContract) GetDrift(ctx contractapi.TransactionContextInterface, driftID string) (*DriftAsset, error) {
	data, _ := ctx.GetStub().GetState("DRIFT_" + driftID)
	if data == nil {
		return nil, fmt.Errorf("derive %s introuvable", driftID)
	}
	var drift DriftAsset
	json.Unmarshal(data, &drift)
	return &drift, nil
}

func (c *ModelGovernanceContract) GetModelHistory(ctx contractapi.TransactionContextInterface, modelID string) (string, error) {
	iterator, err := ctx.GetStub().GetHistoryForKey("MODEL_" + modelID)
	if err != nil {
		return "", err
	}
	defer iterator.Close()
	type Entry struct {
		TxID      string      `json:"txID"`
		Timestamp string      `json:"timestamp"`
		Model     *ModelAsset `json:"model"`
	}
	var history []Entry
	for iterator.HasNext() {
		h, _ := iterator.Next()
		var model ModelAsset
		json.Unmarshal(h.Value, &model)
		history = append(history, Entry{TxID: h.TxId, Timestamp: time.Unix(h.Timestamp.Seconds, 0).Format(time.RFC3339), Model: &model})
	}
	result, _ := json.MarshalIndent(history, "", "  ")
	return string(result), nil
}

func main() {
	cc, err := contractapi.NewChaincode(&ModelGovernanceContract{})
	if err != nil {
		fmt.Printf("Erreur: %v\n", err)
		return
	}
	cc.Start()
}
