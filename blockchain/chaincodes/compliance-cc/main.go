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

type ComplianceReport struct {
	ReportID             string  `json:"reportID"`
	Period               string  `json:"period"`
	GeneratedBy          string  `json:"generatedBy"`
	GeneratedAt          string  `json:"generatedAt"`
	TotalDecisions       int     `json:"totalDecisions"`
	TotalFraudes         int     `json:"totalFraudes"`
	TotalAmbigus         int     `json:"totalAmbigus"`
	TotalLegitimes       int     `json:"totalLegitimes"`
	TotalBloquees        int     `json:"totalBloquees"`
	TauxFraude           float64 `json:"tauxFraude"`
	TotalClaims          int     `json:"totalClaims"`
	TotalClaimsApproved  int     `json:"totalClaimsApproved"`
	TotalClaimsRejected  int     `json:"totalClaimsRejected"`
	AUCMoyen             float64 `json:"aucMoyen"`
	ModeleActif          string  `json:"modeleActif"`
	MLflowRunID          string  `json:"mlflowRunID"`
	DataHashDVC          string  `json:"dataHashDVC"`
	ModelCardCID         string  `json:"modelCardCID"`
	TotalCollusionAlerts int     `json:"totalCollusionAlerts"`
	TotalSLABreaches     int     `json:"totalSLABreaches"`
	TotalDriftEvents     int     `json:"totalDriftEvents"`
	TotalDriftOpen       int     `json:"totalDriftOpen"`
	Status               string  `json:"status"`
	CertifiedBy          string  `json:"certifiedBy"`
	CertifiedAt          string  `json:"certifiedAt"`
	AuditorCert          string  `json:"auditorCert"`
	Anomaly              string  `json:"anomaly"`
}

type InspectionRequest struct {
	RequestID   string `json:"requestID"`
	ReportID    string `json:"reportID"`
	RequestedBy string `json:"requestedBy"`
	RequestedAt string `json:"requestedAt"`
	Anomaly     string `json:"anomaly"`
	Findings    string `json:"findings"`
	Status      string `json:"status"`
	ClosedAt    string `json:"closedAt"`
}

type ComplianceContract struct {
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

func (c *ComplianceContract) InitLedger(
	ctx contractapi.TransactionContextInterface) error {
	fmt.Println("Compliance ledger initialise")
	return nil
}

func (c *ComplianceContract) GenerateReport(
	ctx contractapi.TransactionContextInterface,
	reportID, period,
	totalDecisionsStr, totalFraudesStr, totalAmbigusStr,
	totalLegitimesStr, totalBloqueesStr,
	totalClaimsStr, totalClaimsApprovedStr, totalClaimsRejectedStr,
	totalCollusionAlertsStr, totalSLABreachesStr,
	totalDriftEventsStr, totalDriftOpenStr,
	aucMoyenStr,
	modeleActif, mlflowRunID, dataHashDVC, modelCardCID string) error {

	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User5@bank.fraud-governance.com") {
		return fmt.Errorf("REJET seul User5@bank peut generer un rapport signataire: %s", callerID)
	}

	existing, _ := ctx.GetStub().GetState("REPORT_" + reportID)
	if existing != nil {
		return fmt.Errorf("rapport %s existe deja", reportID)
	}

	totalDecisions, _       := strconv.Atoi(totalDecisionsStr)
	totalFraudes, _         := strconv.Atoi(totalFraudesStr)
	totalAmbigus, _         := strconv.Atoi(totalAmbigusStr)
	totalLegitimes, _       := strconv.Atoi(totalLegitimesStr)
	totalBloquees, _        := strconv.Atoi(totalBloqueesStr)
	totalClaims, _          := strconv.Atoi(totalClaimsStr)
	totalClaimsApproved, _  := strconv.Atoi(totalClaimsApprovedStr)
	totalClaimsRejected, _  := strconv.Atoi(totalClaimsRejectedStr)
	totalCollusionAlerts, _ := strconv.Atoi(totalCollusionAlertsStr)
	totalSLABreaches, _     := strconv.Atoi(totalSLABreachesStr)
	totalDriftEvents, _     := strconv.Atoi(totalDriftEventsStr)
	totalDriftOpen, _       := strconv.Atoi(totalDriftOpenStr)
	aucMoyen, _             := strconv.ParseFloat(aucMoyenStr, 64)

	tauxFraude := 0.0
	if totalDecisions > 0 {
		tauxFraude = float64(totalFraudes) / float64(totalDecisions) * 100
	}

	anomalies := []string{}
	if tauxFraude > 2.0 {
		anomalies = append(anomalies, "TAUX_FRAUDE_CRITIQUE")
	}
	if totalDriftOpen > 0 {
		anomalies = append(anomalies, "DRIFT_NON_TRAITE")
	}
	if totalCollusionAlerts > 0 {
		anomalies = append(anomalies, "COLLUSION_DETECTEE")
	}
	anomaly := strings.Join(anomalies, " | ")

	report := ComplianceReport{
		ReportID:             reportID,
		Period:               period,
		GeneratedBy:          callerID,
		GeneratedAt:          getTxTime(ctx),
		TotalDecisions:       totalDecisions,
		TotalFraudes:         totalFraudes,
		TotalAmbigus:         totalAmbigus,
		TotalLegitimes:       totalLegitimes,
		TotalBloquees:        totalBloquees,
		TauxFraude:           tauxFraude,
		TotalClaims:          totalClaims,
		TotalClaimsApproved:  totalClaimsApproved,
		TotalClaimsRejected:  totalClaimsRejected,
		AUCMoyen:             aucMoyen,
		ModeleActif:          modeleActif,
		MLflowRunID:          mlflowRunID,
		DataHashDVC:          dataHashDVC,
		ModelCardCID:         modelCardCID,
		TotalCollusionAlerts: totalCollusionAlerts,
		TotalSLABreaches:     totalSLABreaches,
		TotalDriftEvents:     totalDriftEvents,
		TotalDriftOpen:       totalDriftOpen,
		Status:               "DRAFT",
		Anomaly:              anomaly,
	}

	data, _ := json.Marshal(report)
	ctx.GetStub().PutState("REPORT_"+reportID, data)
	ctx.GetStub().SetEvent("REPORT_GENERATED", data)
	return nil
}

func (c *ComplianceContract) CertifyReport(
	ctx contractapi.TransactionContextInterface,
	reportID, auditorCert string) error {

	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User1@audit.fraud-governance.com") {
		return fmt.Errorf("REJET seul User1@audit peut certifier signataire: %s", callerID)
	}

	data, _ := ctx.GetStub().GetState("REPORT_" + reportID)
	if data == nil {
		return fmt.Errorf("rapport %s introuvable", reportID)
	}
	var report ComplianceReport
	json.Unmarshal(data, &report)

	if report.Status != "DRAFT" {
		return fmt.Errorf("REJET seul un rapport DRAFT peut etre certifie statut: %s", report.Status)
	}

	report.Status = "CERTIFIED"
	report.CertifiedBy = callerID
	report.CertifiedAt = getTxTime(ctx)
	report.AuditorCert = auditorCert

	newData, _ := json.Marshal(report)
	ctx.GetStub().PutState("REPORT_"+reportID, newData)
	ctx.GetStub().SetEvent("REPORT_CERTIFIED", newData)
	return nil
}

func (c *ComplianceContract) PublishToRegulator(
	ctx contractapi.TransactionContextInterface,
	reportID string) error {

	data, _ := ctx.GetStub().GetState("REPORT_" + reportID)
	if data == nil {
		return fmt.Errorf("rapport %s introuvable", reportID)
	}
	var report ComplianceReport
	json.Unmarshal(data, &report)

	if report.Status != "CERTIFIED" {
		return fmt.Errorf("REJET seul un rapport CERTIFIED peut etre publie statut: %s", report.Status)
	}

	report.Status = "PUBLISHED"
	newData, _ := json.Marshal(report)
	ctx.GetStub().PutState("REPORT_"+reportID, newData)
	ctx.GetStub().SetEvent("REPORT_PUBLISHED_TO_REGULATOR", newData)
	return nil
}

// ─────────────────────────────────────────────
// FONCTION — CopyReportToRegulatory
// Copie le rapport sur regulatory-channel
// ─────────────────────────────────────────────

func (c *ComplianceContract) CopyReportToRegulatory(
	ctx contractapi.TransactionContextInterface,
	reportID, period,
	totalDecisionsStr, totalFraudesStr, totalAmbigusStr,
	totalLegitimesStr, totalBloqueesStr,
	totalClaimsStr, totalClaimsApprovedStr, totalClaimsRejectedStr,
	totalCollusionAlertsStr, totalSLABreachesStr,
	totalDriftEventsStr, totalDriftOpenStr,
	aucMoyenStr,
	modeleActif, mlflowRunID, dataHashDVC, modelCardCID,
	generatedBy, certifiedBy, auditorCert string) error {

	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User1@audit.fraud-governance.com") {
		return fmt.Errorf("REJET seul User1@audit peut copier sur regulatory signataire: %s", callerID)
	}

	totalDecisions, _       := strconv.Atoi(totalDecisionsStr)
	totalFraudes, _         := strconv.Atoi(totalFraudesStr)
	totalAmbigus, _         := strconv.Atoi(totalAmbigusStr)
	totalLegitimes, _       := strconv.Atoi(totalLegitimesStr)
	totalBloquees, _        := strconv.Atoi(totalBloqueesStr)
	totalClaims, _          := strconv.Atoi(totalClaimsStr)
	totalClaimsApproved, _  := strconv.Atoi(totalClaimsApprovedStr)
	totalClaimsRejected, _  := strconv.Atoi(totalClaimsRejectedStr)
	totalCollusionAlerts, _ := strconv.Atoi(totalCollusionAlertsStr)
	totalSLABreaches, _     := strconv.Atoi(totalSLABreachesStr)
	totalDriftEvents, _     := strconv.Atoi(totalDriftEventsStr)
	totalDriftOpen, _       := strconv.Atoi(totalDriftOpenStr)
	aucMoyen, _             := strconv.ParseFloat(aucMoyenStr, 64)

	tauxFraude := 0.0
	if totalDecisions > 0 {
		tauxFraude = float64(totalFraudes) / float64(totalDecisions) * 100
	}

	anomalies := []string{}
	if tauxFraude > 2.0 {
		anomalies = append(anomalies, "TAUX_FRAUDE_CRITIQUE")
	}
	if totalDriftOpen > 0 {
		anomalies = append(anomalies, "DRIFT_NON_TRAITE")
	}
	if totalCollusionAlerts > 0 {
		anomalies = append(anomalies, "COLLUSION_DETECTEE")
	}

	report := ComplianceReport{
		ReportID:             reportID,
		Period:               period,
		GeneratedBy:          generatedBy,
		GeneratedAt:          getTxTime(ctx),
		TotalDecisions:       totalDecisions,
		TotalFraudes:         totalFraudes,
		TotalAmbigus:         totalAmbigus,
		TotalLegitimes:       totalLegitimes,
		TotalBloquees:        totalBloquees,
		TauxFraude:           tauxFraude,
		TotalClaims:          totalClaims,
		TotalClaimsApproved:  totalClaimsApproved,
		TotalClaimsRejected:  totalClaimsRejected,
		AUCMoyen:             aucMoyen,
		ModeleActif:          modeleActif,
		MLflowRunID:          mlflowRunID,
		DataHashDVC:          dataHashDVC,
		ModelCardCID:         modelCardCID,
		TotalCollusionAlerts: totalCollusionAlerts,
		TotalSLABreaches:     totalSLABreaches,
		TotalDriftEvents:     totalDriftEvents,
		TotalDriftOpen:       totalDriftOpen,
		Status:               "PUBLISHED",
		CertifiedBy:          certifiedBy,
		CertifiedAt:          getTxTime(ctx),
		AuditorCert:          auditorCert,
		Anomaly:              strings.Join(anomalies, " | "),
	}

	data, _ := json.Marshal(report)
	ctx.GetStub().PutState("REPORT_"+reportID, data)
	ctx.GetStub().SetEvent("REPORT_COPIED_TO_REGULATORY", data)
	return nil
}

func (c *ComplianceContract) RequestInspection(
	ctx contractapi.TransactionContextInterface,
	requestID, reportID, anomaly string) error {

	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User1@regulator.fraud-governance.com") {
		return fmt.Errorf("REJET seul User1@regulator peut demander une inspection signataire: %s", callerID)
	}

	data, _ := ctx.GetStub().GetState("REPORT_" + reportID)
	if data == nil {
		return fmt.Errorf("rapport %s introuvable", reportID)
	}
	var report ComplianceReport
	json.Unmarshal(data, &report)

	if report.Status != "PUBLISHED" {
		return fmt.Errorf("REJET rapport doit etre PUBLISHED statut: %s", report.Status)
	}

	request := InspectionRequest{
		RequestID:   requestID,
		ReportID:    reportID,
		RequestedBy: callerID,
		RequestedAt: getTxTime(ctx),
		Anomaly:     anomaly,
		Status:      "OPEN",
	}

	reqData, _ := json.Marshal(request)
	ctx.GetStub().PutState("INSPECTION_"+requestID, reqData)
	ctx.GetStub().SetEvent("INSPECTION_REQUESTED", reqData)
	return nil
}

func (c *ComplianceContract) SubmitInspectionReport(
	ctx contractapi.TransactionContextInterface,
	requestID, findings string) error {

	callerID, err := getCallerID(ctx)
	if err != nil {
		return err
	}
	if !strings.Contains(callerID, "User1@audit.fraud-governance.com") {
		return fmt.Errorf("REJET seul User1@audit peut soumettre un rapport d'inspection signataire: %s", callerID)
	}

	data, _ := ctx.GetStub().GetState("INSPECTION_" + requestID)
	if data == nil {
		return fmt.Errorf("inspection %s introuvable", requestID)
	}
	var request InspectionRequest
	json.Unmarshal(data, &request)

	if request.Status != "OPEN" {
		return fmt.Errorf("inspection %s deja fermee", requestID)
	}

	request.Findings = findings
	request.Status = "CLOSED"
	request.ClosedAt = getTxTime(ctx)

	newData, _ := json.Marshal(request)
	ctx.GetStub().PutState("INSPECTION_"+requestID, newData)
	ctx.GetStub().SetEvent("INSPECTION_CLOSED", newData)
	return nil
}

func (c *ComplianceContract) GetReport(
	ctx contractapi.TransactionContextInterface,
	reportID string) (*ComplianceReport, error) {

	data, _ := ctx.GetStub().GetState("REPORT_" + reportID)
	if data == nil {
		return nil, fmt.Errorf("rapport %s introuvable", reportID)
	}
	var report ComplianceReport
	json.Unmarshal(data, &report)
	return &report, nil
}

func (c *ComplianceContract) GetInspection(
	ctx contractapi.TransactionContextInterface,
	requestID string) (*InspectionRequest, error) {

	data, _ := ctx.GetStub().GetState("INSPECTION_" + requestID)
	if data == nil {
		return nil, fmt.Errorf("inspection %s introuvable", requestID)
	}
	var request InspectionRequest
	json.Unmarshal(data, &request)
	return &request, nil
}

func main() {
	cc, err := contractapi.NewChaincode(&ComplianceContract{})
	if err != nil {
		fmt.Printf("Erreur: %v\n", err)
		return
	}
	cc.Start()
}