package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type FraudDecision struct {
	TxID          string  `json:"txID"`
	Score         float64 `json:"score"`
	Zone          string  `json:"zone"`
	ShapHash      string  `json:"shapHash"`
	ModelID       string  `json:"modelID"`
	CardID        string  `json:"cardID"`
	ClientID      string  `json:"clientID"`
	RecordedAt    string  `json:"recordedAt"`
	Decision      string  `json:"decision"`
	AnalystID     string  `json:"analystID"`
	Justification string  `json:"justification"`
	UpdatedAt     string  `json:"updatedAt"`
}

type BlockHistoryEntry struct {
	TxID          string  `json:"txID"`
	Action        string  `json:"action"`
	Reason        string  `json:"reason"`
	ShapHash      string  `json:"shapHash"`
	Score         float64 `json:"score"`
	ActionAt      string  `json:"actionAt"`
	ActionBy      string  `json:"actionBy"`
	Justification string  `json:"justification"`
}

type CardAsset struct {
	CardID          string              `json:"cardID"`
	ClientID        string              `json:"clientID"`
	Status          string              `json:"status"`
	BlockReason     string              `json:"blockReason"`
	BlockedAt       string              `json:"blockedAt"`
	ExpiresAt       string              `json:"expiresAt"`
	CurrentTxID     string              `json:"currentTxID"`
	CurrentShapHash string              `json:"currentShapHash"`
	CurrentScore    float64             `json:"currentScore"`
	BlockHistory    []BlockHistoryEntry `json:"blockHistory"`
}

type RiskProfile struct {
	ClientID          string `json:"clientID"`
	TotalTransactions int    `json:"totalTransactions"`
	TotalFraudes      int    `json:"totalFraudes"`
	TotalAmbigus      int    `json:"totalAmbigus"`
	RiskScore         string `json:"riskScore"`
	LastUpdated       string `json:"lastUpdated"`
}

type AnalystAction struct {
	TxID         string `json:"txID"`
	AssignedTo   string `json:"assignedTo"`
	AssignedAt   string `json:"assignedAt"`
	DecidedAt    string `json:"decidedAt"`
	ResponseTime string `json:"responseTime"`
	SLARespected bool   `json:"slaRespected"`
}

type CollusionTracker struct {
	AnalystID    string   `json:"analystID"`
	ClientID     string   `json:"clientID"`
	Month        string   `json:"month"`
	Count        int      `json:"count"`
	Transactions []string `json:"transactions"`
}

type CollusionAlert struct {
	AnalystID  string `json:"analystID"`
	ClientID   string `json:"clientID"`
	Count      int    `json:"count"`
	Period     string `json:"period"`
	DetectedAt string `json:"detectedAt"`
}

type ClaimAsset struct {
	ClaimID       string `json:"claimID"`
	TxID          string `json:"txID"`
	CardID        string `json:"cardID"`
	ClientID      string `json:"clientID"`
	ClaimedBy     string `json:"claimedBy"`
	ClaimedAt     string `json:"claimedAt"`
	Reason        string `json:"reason"`
	Status        string `json:"status"`
	DecidedBy     string `json:"decidedBy"`
	DecidedAt     string `json:"decidedAt"`
	Resolution    string `json:"resolution"`
	Justification string `json:"justification"`
}

type AnalystThreshold struct {
	MaxDailyCorrections   int    `json:"maxDailyCorrections"`
	MaxFavorablePerClient int    `json:"maxFavorablePerClient"`
	SLAHours              int    `json:"slaHours"`
	AmbiguThreshold       int    `json:"ambiguThreshold"`
	ApprovedBy            string `json:"approvedBy"`
	ReviewDeadline        string `json:"reviewDeadline"`
}

type FraudDetectionContract struct {
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

func (c *FraudDetectionContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	threshold := AnalystThreshold{
		MaxDailyCorrections:   10,
		MaxFavorablePerClient: 3,
		SLAHours:              4,
		AmbiguThreshold:       5,
		ApprovedBy:            "SYSTEM",
		ReviewDeadline:        time.Now().AddDate(0, 6, 0).Format(time.RFC3339),
	}
	data, _ := json.Marshal(threshold)
	return ctx.GetStub().PutState("ANALYST_THRESHOLD", data)
}

func (c *FraudDetectionContract) blockCard(ctx contractapi.TransactionContextInterface, cardID, clientID, reason, duration, txID, shapHash, actionBy string, score float64) error {
	data, _ := ctx.GetStub().GetState("CARD_" + cardID)
	var card CardAsset
	if data != nil {
		json.Unmarshal(data, &card)
	} else {
		card = CardAsset{CardID: cardID, ClientID: clientID, BlockHistory: []BlockHistoryEntry{}}
	}
	now := getTxTime(ctx)
	expiresAt := ""
	if duration == "48h" {
		t, _ := time.Parse(time.RFC3339, now)
		expiresAt = t.Add(48 * time.Hour).Format(time.RFC3339)
	}
	card.Status = "BLOCKED"
	card.BlockReason = reason
	card.BlockedAt = now
	card.ExpiresAt = expiresAt
	card.CurrentTxID = txID
	card.CurrentShapHash = shapHash
	card.CurrentScore = score
	card.BlockHistory = append(card.BlockHistory, BlockHistoryEntry{TxID: txID, Action: "BLOCKED", Reason: reason, ShapHash: shapHash, Score: score, ActionAt: now, ActionBy: actionBy})
	newData, _ := json.Marshal(card)
	return ctx.GetStub().PutState("CARD_"+cardID, newData)
}

func (c *FraudDetectionContract) unblockCard(ctx contractapi.TransactionContextInterface, cardID, unblockedBy, reason, justification string) error {
	data, _ := ctx.GetStub().GetState("CARD_" + cardID)
	if data == nil {
		return nil
	}
	var card CardAsset
	json.Unmarshal(data, &card)
	card.Status = "ACTIVE"
	card.BlockReason = ""
	card.ExpiresAt = ""
	card.CurrentTxID = ""
	card.CurrentShapHash = ""
	card.CurrentScore = 0
	card.BlockHistory = append(card.BlockHistory, BlockHistoryEntry{Action: "UNBLOCKED", Reason: reason, ActionAt: getTxTime(ctx), ActionBy: unblockedBy, Justification: justification})
	newData, _ := json.Marshal(card)
	ctx.GetStub().PutState("CARD_"+cardID, newData)
	ctx.GetStub().SetEvent("CARD_UNBLOCKED", newData)
	return nil
}

func (c *FraudDetectionContract) checkCardExpiry(ctx contractapi.TransactionContextInterface, cardID string) {
	data, _ := ctx.GetStub().GetState("CARD_" + cardID)
	if data == nil {
		return
	}
	var card CardAsset
	json.Unmarshal(data, &card)
	if card.Status != "BLOCKED" || card.ExpiresAt == "" {
		return
	}
	expiry, err := time.Parse(time.RFC3339, card.ExpiresAt)
	if err != nil {
		return
	}
	if time.Now().After(expiry) {
		c.unblockCard(ctx, cardID, "SYSTEM", "expiration", "blocage 48h expire")
	}
}

func (c *FraudDetectionContract) updateRiskProfile(ctx contractapi.TransactionContextInterface, clientID, zone string) {
	data, _ := ctx.GetStub().GetState("RISK_PROFILE_" + clientID)
	var profile RiskProfile
	if data != nil {
		json.Unmarshal(data, &profile)
	} else {
		profile = RiskProfile{ClientID: clientID}
	}
	profile.TotalTransactions++
	if zone == "FRAUDE" {
		profile.TotalFraudes++
	}
	if zone == "AMBIGU" {
		profile.TotalAmbigus++
	}
	taux := 0.0
	if profile.TotalTransactions > 0 {
		taux = float64(profile.TotalFraudes) / float64(profile.TotalTransactions) * 100
	}
	if taux < 5 {
		profile.RiskScore = "LOW"
	} else if taux < 15 {
		profile.RiskScore = "MEDIUM"
	} else {
		profile.RiskScore = "HIGH"
	}
	profile.LastUpdated = getTxTime(ctx)
	newData, _ := json.Marshal(profile)
	ctx.GetStub().PutState("RISK_PROFILE_"+clientID, newData)
}

func (c *FraudDetectionContract) detectCollusion(ctx contractapi.TransactionContextInterface, analystID, clientID, txID string) bool {
	threshData, _ := ctx.GetStub().GetState("ANALYST_THRESHOLD")
	var threshold AnalystThreshold
	threshold.MaxFavorablePerClient = 3
	if threshData != nil {
		json.Unmarshal(threshData, &threshold)
	}
	month := time.Now().Format("2006-01")
	key := "COLLUSION_TRACKER_" + analystID + "_" + clientID + "_" + month
	data, _ := ctx.GetStub().GetState(key)
	var tracker CollusionTracker
	if data != nil {
		json.Unmarshal(data, &tracker)
	} else {
		tracker = CollusionTracker{AnalystID: analystID, ClientID: clientID, Month: month, Transactions: []string{}}
	}
	tracker.Count++
	tracker.Transactions = append(tracker.Transactions, txID)
	newData, _ := json.Marshal(tracker)
	ctx.GetStub().PutState(key, newData)
	if tracker.Count > threshold.MaxFavorablePerClient {
		alert := CollusionAlert{AnalystID: analystID, ClientID: clientID, Count: tracker.Count, Period: month, DetectedAt: getTxTime(ctx)}
		alertData, _ := json.Marshal(alert)
		ctx.GetStub().PutState("COLLUSION_ALERT_"+analystID+"_"+clientID, alertData)
		ctx.GetStub().SetEvent("COLLUSION_DETECTED", alertData)
		return true
	}
	return false
}

func (c *FraudDetectionContract) countTodayCorrections(ctx contractapi.TransactionContextInterface, analystID string) int {
	today := time.Now().Format("2006-01-02")
	key := "CORRECTIONS_" + analystID + "_" + today
	data, _ := ctx.GetStub().GetState(key)
	count := 0
	if data != nil {
		json.Unmarshal(data, &count)
	}
	count++
	newData, _ := json.Marshal(count)
	ctx.GetStub().PutState(key, newData)
	return count
}

func (c *FraudDetectionContract) RecordDecision(ctx contractapi.TransactionContextInterface, txID, zone, shapHash, modelID, cardID, clientID, scoreStr string) error {
	score, err := strconv.ParseFloat(scoreStr, 64)
	if err != nil {
		return fmt.Errorf("score invalide: %s", scoreStr)
	}
	existing, _ := ctx.GetStub().GetState("DECISION_" + txID)
	if existing != nil {
		return fmt.Errorf("decision %s existe deja", txID)
	}
	validZones := map[string]bool{"LEGITIME": true, "AMBIGU": true, "FRAUDE": true}
	if !validZones[zone] {
		return fmt.Errorf("zone invalide: %s", zone)
	}
	c.checkCardExpiry(ctx, cardID)
	c.updateRiskProfile(ctx, clientID, zone)
	decision := FraudDecision{TxID: txID, Score: score, Zone: zone, ShapHash: shapHash, ModelID: modelID, CardID: cardID, ClientID: clientID, RecordedAt: getTxTime(ctx), Decision: zone}
	switch zone {
	case "FRAUDE":
		c.blockCard(ctx, cardID, clientID, "AUTO_FRAUD", "permanent", txID, shapHash, "SYSTEM", score)
		ctx.GetStub().SetEvent("FRAUD_AUTO_BLOCKED", []byte(txID))
	case "AMBIGU":
		today := time.Now().Format("2006-01-02")
		countKey := "AMBIGU_COUNT_" + cardID + "_" + today
		data, _ := ctx.GetStub().GetState(countKey)
		count := 0
		if data != nil {
			json.Unmarshal(data, &count)
		}
		count++
		newData, _ := json.Marshal(count)
		ctx.GetStub().PutState(countKey, newData)
		threshData, _ := ctx.GetStub().GetState("ANALYST_THRESHOLD")
		var threshold AnalystThreshold
		threshold.AmbiguThreshold = 5
		if threshData != nil {
			json.Unmarshal(threshData, &threshold)
		}
		if count >= threshold.AmbiguThreshold {
			c.blockCard(ctx, cardID, clientID, "MULTIPLE_AMBIGUOUS", "48h", txID, shapHash, "SYSTEM", score)
			ctx.GetStub().SetEvent("CARD_BLOCKED_MULTIPLE_AMBIGU", []byte(cardID))
		} else {
			action := AnalystAction{TxID: txID, AssignedTo: "User4@bank.fraud-governance.com", AssignedAt: getTxTime(ctx)}
			actionData, _ := json.Marshal(action)
			ctx.GetStub().PutState("ANALYST_ACTION_"+txID, actionData)
			ctx.GetStub().SetEvent("AMBIGU_ALERT", []byte(txID))
		}
	}
	data, _ := json.Marshal(decision)
	ctx.GetStub().PutState("DECISION_"+txID, data)
	ctx.GetStub().SetEvent("DECISION_RECORDED", data)
	return nil
}

func (c *FraudDetectionContract) ConfirmFraud(ctx contractapi.TransactionContextInterface, txID, justification string) error {
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User4@bank.fraud-governance.com") {
		return fmt.Errorf("REJET seul User4@bank peut confirmer signataire: %s", callerID)
	}
	data, _ := ctx.GetStub().GetState("DECISION_" + txID)
	if data == nil {
		return fmt.Errorf("decision %s introuvable", txID)
	}
	var decision FraudDecision
	json.Unmarshal(data, &decision)
	if decision.Zone != "AMBIGU" {
		return fmt.Errorf("REJET seule une decision AMBIGU peut etre confirmee zone: %s", decision.Zone)
	}
	if c.detectCollusion(ctx, callerID, decision.ClientID, txID) {
		return fmt.Errorf("REJET collusion detectee analyste %s client %s", callerID, decision.ClientID)
	}
	actionData, _ := ctx.GetStub().GetState("ANALYST_ACTION_" + txID)
	if actionData != nil {
		var action AnalystAction
		json.Unmarshal(actionData, &action)
		assigned, _ := time.Parse(time.RFC3339, action.AssignedAt)
		now, _ := time.Parse(time.RFC3339, getTxTime(ctx))
		responseTime := now.Sub(assigned)
		threshData, _ := ctx.GetStub().GetState("ANALYST_THRESHOLD")
		var threshold AnalystThreshold
		threshold.SLAHours = 4
		if threshData != nil {
			json.Unmarshal(threshData, &threshold)
		}
		action.DecidedAt = getTxTime(ctx)
		action.ResponseTime = responseTime.String()
		action.SLARespected = responseTime.Hours() <= float64(threshold.SLAHours)
		if !action.SLARespected {
			ctx.GetStub().SetEvent("SLA_BREACH", []byte(txID))
		}
		newActionData, _ := json.Marshal(action)
		ctx.GetStub().PutState("ANALYST_ACTION_"+txID, newActionData)
	}
	c.blockCard(ctx, decision.CardID, decision.ClientID, "ANALYST_DECISION", "permanent", txID, decision.ShapHash, callerID, decision.Score)
	decision.Decision = "FRAUDE"
	decision.AnalystID = callerID
	decision.Justification = justification
	decision.UpdatedAt = getTxTime(ctx)
	newData, _ := json.Marshal(decision)
	ctx.GetStub().PutState("DECISION_"+txID, newData)
	ctx.GetStub().SetEvent("FRAUD_CONFIRMED", newData)
	return nil
}

func (c *FraudDetectionContract) RejectFraud(ctx contractapi.TransactionContextInterface, txID, justification string) error {
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User4@bank.fraud-governance.com") {
		return fmt.Errorf("REJET seul User4@bank peut rejeter signataire: %s", callerID)
	}
	data, _ := ctx.GetStub().GetState("DECISION_" + txID)
	if data == nil {
		return fmt.Errorf("decision %s introuvable", txID)
	}
	var decision FraudDecision
	json.Unmarshal(data, &decision)
	if decision.Zone != "AMBIGU" {
		return fmt.Errorf("REJET seule une decision AMBIGU peut etre rejetee zone: %s", decision.Zone)
	}
	if c.detectCollusion(ctx, callerID, decision.ClientID, txID) {
		return fmt.Errorf("REJET collusion detectee analyste %s client %s", callerID, decision.ClientID)
	}
	c.unblockCard(ctx, decision.CardID, callerID, "analyst_reject", justification)
	decision.Decision = "LEGITIME"
	decision.AnalystID = callerID
	decision.Justification = justification
	decision.UpdatedAt = getTxTime(ctx)
	newData, _ := json.Marshal(decision)
	ctx.GetStub().PutState("DECISION_"+txID, newData)
	ctx.GetStub().SetEvent("FRAUD_REJECTED", newData)
	return nil
}

func (c *FraudDetectionContract) CorrectDecision(ctx contractapi.TransactionContextInterface, txID, newDecision, reason string) error {
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User4@bank.fraud-governance.com") {
		return fmt.Errorf("REJET seul User4@bank peut corriger signataire: %s", callerID)
	}
	threshData, _ := ctx.GetStub().GetState("ANALYST_THRESHOLD")
	var threshold AnalystThreshold
	threshold.MaxDailyCorrections = 10
	if threshData != nil {
		json.Unmarshal(threshData, &threshold)
	}
	count := c.countTodayCorrections(ctx, callerID)
	if count >= threshold.MaxDailyCorrections {
		alert := fmt.Sprintf("ALERTE %s depasse %d corrections", callerID, threshold.MaxDailyCorrections)
		ctx.GetStub().SetEvent("ANALYST_THRESHOLD_EXCEEDED", []byte(alert))
		return fmt.Errorf("REJET seuil journalier %d depasse pour %s", threshold.MaxDailyCorrections, callerID)
	}
	data, _ := ctx.GetStub().GetState("DECISION_" + txID)
	if data == nil {
		return fmt.Errorf("decision %s introuvable", txID)
	}
	var decision FraudDecision
	json.Unmarshal(data, &decision)
	if c.detectCollusion(ctx, callerID, decision.ClientID, txID) {
		return fmt.Errorf("REJET collusion detectee analyste %s client %s", callerID, decision.ClientID)
	}
	if newDecision == "LEGITIME" {
		c.unblockCard(ctx, decision.CardID, callerID, "correction", reason)
	}
	decision.Decision = newDecision
	decision.AnalystID = callerID
	decision.Justification = reason
	decision.UpdatedAt = getTxTime(ctx)
	newData, _ := json.Marshal(decision)
	ctx.GetStub().PutState("DECISION_"+txID, newData)
	ctx.GetStub().SetEvent("DECISION_CORRECTED", newData)
	return nil
}

func (c *FraudDetectionContract) SubmitClaim(ctx contractapi.TransactionContextInterface, claimID, txID, cardID, clientID, reason string) error {
	txData, _ := ctx.GetStub().GetState("DECISION_" + txID)
	if txData == nil {
		return fmt.Errorf("transaction %s introuvable", txID)
	}
	cardData, _ := ctx.GetStub().GetState("CARD_" + cardID)
	if cardData == nil {
		return fmt.Errorf("carte %s introuvable", cardID)
	}
	var card CardAsset
	json.Unmarshal(cardData, &card)
	if card.Status != "BLOCKED" {
		return fmt.Errorf("REJET carte %s n'est pas bloquee", cardID)
	}
	claim := ClaimAsset{ClaimID: claimID, TxID: txID, CardID: cardID, ClientID: clientID, ClaimedBy: clientID, ClaimedAt: getTxTime(ctx), Reason: reason, Status: "PENDING"}
	data, _ := json.Marshal(claim)
	ctx.GetStub().PutState("CLAIM_"+claimID, data)
	ctx.GetStub().SetEvent("CLAIM_SUBMITTED", data)
	return nil
}

func (c *FraudDetectionContract) ProcessClaim(ctx contractapi.TransactionContextInterface, claimID, resolution, justification string) error {
	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User4@bank.fraud-governance.com") {
		return fmt.Errorf("REJET seul User4@bank peut traiter une reclamation signataire: %s", callerID)
	}
	data, _ := ctx.GetStub().GetState("CLAIM_" + claimID)
	if data == nil {
		return fmt.Errorf("reclamation %s introuvable", claimID)
	}
	var claim ClaimAsset
	json.Unmarshal(data, &claim)
	if claim.Status != "PENDING" {
		return fmt.Errorf("REJET reclamation %s deja traitee statut: %s", claimID, claim.Status)
	}
	if c.detectCollusion(ctx, callerID, claim.ClientID, claim.TxID) {
		return fmt.Errorf("REJET collusion detectee analyste %s client %s", callerID, claim.ClientID)
	}
	claim.DecidedBy = callerID
	claim.DecidedAt = getTxTime(ctx)
	claim.Justification = justification
	if resolution == "APPROVED" {
		c.unblockCard(ctx, claim.CardID, callerID, "claim_approved", justification)
		claim.Status = "APPROVED"
		claim.Resolution = "UNBLOCKED"
	} else {
		claim.Status = "REJECTED"
		claim.Resolution = "MAINTAINED"
	}
	newData, _ := json.Marshal(claim)
	ctx.GetStub().PutState("CLAIM_"+claimID, newData)
	ctx.GetStub().SetEvent("CLAIM_PROCESSED", newData)
	return nil
}

func (c *FraudDetectionContract) GetCardStatus(ctx contractapi.TransactionContextInterface, cardID string) (*CardAsset, error) {
	data, _ := ctx.GetStub().GetState("CARD_" + cardID)
	if data == nil {
		return nil, fmt.Errorf("carte %s introuvable", cardID)
	}
	var card CardAsset
	json.Unmarshal(data, &card)
	return &card, nil
}

func (c *FraudDetectionContract) GetDecision(ctx contractapi.TransactionContextInterface, txID string) (*FraudDecision, error) {
	data, _ := ctx.GetStub().GetState("DECISION_" + txID)
	if data == nil {
		return nil, fmt.Errorf("decision %s introuvable", txID)
	}
	var decision FraudDecision
	json.Unmarshal(data, &decision)
	return &decision, nil
}

func (c *FraudDetectionContract) GetClaim(ctx contractapi.TransactionContextInterface, claimID string) (*ClaimAsset, error) {
	data, _ := ctx.GetStub().GetState("CLAIM_" + claimID)
	if data == nil {
		return nil, fmt.Errorf("reclamation %s introuvable", claimID)
	}
	var claim ClaimAsset
	json.Unmarshal(data, &claim)
	return &claim, nil
}

func (c *FraudDetectionContract) GetRiskProfile(ctx contractapi.TransactionContextInterface, clientID string) (*RiskProfile, error) {
	data, _ := ctx.GetStub().GetState("RISK_PROFILE_" + clientID)
	if data == nil {
		return nil, fmt.Errorf("profil %s introuvable", clientID)
	}
	var profile RiskProfile
	json.Unmarshal(data, &profile)
	return &profile, nil
}

func (c *FraudDetectionContract) GetDecisionHistory(ctx contractapi.TransactionContextInterface, txID string) (string, error) {
	iterator, err := ctx.GetStub().GetHistoryForKey("DECISION_" + txID)
	if err != nil {
		return "", err
	}
	defer iterator.Close()
	type Entry struct {
		TxID      string         `json:"txID"`
		Timestamp string         `json:"timestamp"`
		Decision  *FraudDecision `json:"decision"`
	}
	var history []Entry
	for iterator.HasNext() {
		h, _ := iterator.Next()
		var d FraudDecision
		json.Unmarshal(h.Value, &d)
		history = append(history, Entry{TxID: h.TxId, Timestamp: time.Unix(h.Timestamp.Seconds, 0).Format(time.RFC3339), Decision: &d})
	}
	result, _ := json.MarshalIndent(history, "", "  ")
	return string(result), nil
}

func main() {
	cc, err := contractapi.NewChaincode(&FraudDetectionContract{})
	if err != nil {
		fmt.Printf("Erreur: %v\n", err)
		return
	}
	cc.Start()
}