# BlockML-Gov — AI Governance Platform for Banking

<div align="center">

![Version](https://img.shields.io/badge/version-4.0-042C53?style=flat-square)
![Hyperledger Fabric](https://img.shields.io/badge/Hyperledger_Fabric-2.5-2F9F6B?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-185FA5?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-0db7ed?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-BA7517?style=flat-square)

**An AI model governance platform for the banking sector, built on Hyperledger Fabric, FastAPI, and Streamlit.**

*EU AI Act Compliance · Basel III · Blockchain Traceability · Real-Time Fraud Detection*

</div>

---

## What is BlockML-Gov?

BlockML-Gov is a production-grade, end-to-end AI governance framework designed for regulated banking environments. It combines real-time fraud detection with immutable, blockchain-anchored audit trails — ensuring that every model decision is explainable, traceable, and compliant with regulatory standards.

The platform addresses a core challenge in financial AI: **how do you prove that a model behaved correctly, at a specific moment in time, for a specific transaction?** BlockML-Gov answers this by recording every inference decision, SHAP explanation, drift alert, and human intervention permanently on a permissioned Hyperledger Fabric ledger.

---

## Key Features

- **Real-time fraud scoring** — transactions are enriched, scored, and routed (block / review / approve) in under 100 ms
- **Explainable decisions** — every model output is accompanied by a SHAP explanation vector stored on IPFS, with its content identifier on-chain
- **Immutable audit trail** — Hyperledger Fabric records all decisions, governance events, and regulatory submissions across four dedicated channels
- **Continuous model surveillance** — Evidently AI detects data drift, model drift, and concept drift; all alerts are blockchain-stamped
- **Role-based governance dashboard** — six distinct actor profiles (Data Scientist, ML Engineer, Fraud Analyst, Internal Auditor, External Auditor, Regulator) each see a certified, personalized view
- **Regulatory access** — the Regulator participates as a direct node in the Fabric network, querying the `regulatory-submissions` channel without bank intermediation

---

## System Architecture

BlockML-Gov is organized into eight functional layers:

| Layer | Name | Responsibility |
|---|---|---|
| 1 | Acquisition | Ingests transactions from CBS, TPE/ATM terminals, and Banking API |
| 2 | Transport | Apache Kafka — durable, ordered message delivery with 7-day retention |
| 3 | Enrichment | Apache Flink — real-time feature engineering (time windows, geo-delta, device change) |
| 4 | Inference | FastAPI + Random Forest + SHAP + three-zone decision rule |
| 5 | Immutable Recording | Hyperledger Fabric (4 channels) + IPFS for large artifacts |
| 6 | Model Surveillance | Evidently AI — drift detection and on-chain alerting |
| 7 | Alerts | RabbitMQ — guaranteed delivery to Fraud Analysts, ML Engineers, and Auditors |
| 8 | Interface | Streamlit dashboard with role-based access control |

```
┌─────────────────────────────────────────────────────────────┐
│                     BlockML-Gov v4.0                        │
├──────────────────┬──────────────────┬───────────────────────┤
│  Hyperledger     │  Application     │  Infrastructure       │
│  Fabric 2.5      │  Stack           │                       │
│                  │                  │                       │
│  Orderer         │  FastAPI (API)   │  Redis                │
│  Peer Bank       │  Streamlit (UI)  │  RabbitMQ             │
│  Peer Audit      │  Auth Service    │  MLflow               │
│  Peer Regulator  │  Gateway (Go)    │  Kafka / Flink        │
│  CouchDB x3      │  Drift Monitor   │  CouchDB              │
└──────────────────┴──────────────────┴───────────────────────┘
```

**Hyperledger Fabric Chaincodes:**
- `model-governance-cc` — `modelgovernance` channel
- `fraud-detection-cc` — `frauddetection` channel
- `compliance-cc` — `compliance` and `regulatory` channels

---

## Technology Stack

| Component | Technology |
|---|---|
| Blockchain | Hyperledger Fabric 2.5 |
| ML Inference | scikit-learn (Random Forest) |
| Explainability | SHAP |
| Model Monitoring | Evidently AI |
| API | FastAPI (Python 3.11) |
| Dashboard | Streamlit |
| Stream Processing | Apache Kafka + Apache Flink |
| Distributed Storage | IPFS |
| MLOps | MLflow |
| Messaging | RabbitMQ |
| Auth | JWT + MySQL (WAMP) |
| Cache | Redis |
| Containerization | Docker Compose |

---

## Project Structure

```
fraud-governance-system/
├── api/                        # FastAPI backend
├── auth-service/               # JWT authentication + MySQL
├── blockchain/
│   ├── chaincodes/
│   │   ├── model-governance-cc/
│   │   ├── fraud-detection-cc/
│   │   └── compliance-cc/
│   ├── network/
│   │   ├── docker-compose-fabric.yml
│   │   └── crypto-material/
│   ├── scripts/
│   │   ├── deploy-chaincode.sh
│   │   └── join-channels.sh
│   └── Makefile
├── dashboard/                  # Streamlit frontend
│   ├── app.py
│   ├── auth.py
│   ├── styles.py
│   ├── components/
│   ├── pages/
│   │   ├── admin/
│   │   ├── data_scientist/
│   │   ├── compliance_officer/
│   │   ├── ml_engineer/
│   │   ├── fraud_analyst/
│   │   ├── auditor/
│   │   └── regulator/
│   └── utils/
├── drift/                      # ML drift detection
├── ipfs-service/               # Distributed artifact storage
├── mlops/                      # MLflow pipeline
├── redis/                      # Redis configuration
├── streaming/                  # Kafka producers/consumers
├── docker-compose.yml
└── start-blockmlgov.sh
```

---

## Pre-built Docker Images

Images are available on Docker Hub:

```bash
docker pull asmaeourrai/blockmlgov-api:latest
docker pull asmaeourrai/blockmlgov-dashboard:latest
docker pull asmaeourrai/blockmlgov-auth:latest
```

---

## Documentation

For full setup instructions, configuration details, and troubleshooting, refer to the **[Developer Manual](./DEVELOPER_MANUAL.md)**.

---

## Contributors

| Name | Role |
|---|---|
| Asmae Ourrai | ML pipeline integration, API backend & end-to-end system orchestration |
| Safae El Ouajidi | Blockchain infrastructure, Hyperledger Fabric network, channels & smart contracts |
| Marwa M'haya | ML model development, training & evaluation |

---

<div align="center">

BlockML-Gov v4.0 — PFA Project 2026

*Hyperledger Fabric · FastAPI · Streamlit · MLflow · Kafka*

</div>
