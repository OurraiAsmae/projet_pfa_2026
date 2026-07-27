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

## 📖 Software Description

**BlockML-Gov** is a production-grade, end-to-end AI governance framework designed for regulated banking environments. It combines real-time transaction scoring with immutable, blockchain-anchored audit trails, ensuring every model decision is explainable, traceable, and fully compliant with regulatory standards (such as the EU AI Act and BAM Morocco requirements).

The platform addresses a core challenge in financial AI: **how do you prove that a machine learning model behaved correctly, at a specific moment in time, for a specific transaction?** BlockML-Gov answers this by recording every inference decision, SHAP explanation, drift alert, and human approval permanently on a permissioned Hyperledger Fabric ledger across dedicated channels.

---

## 🛠️ Key Features

- **Real-Time Fraud Scoring** — Transactions are scored and routed (Legitimate, Ambiguous, Fraudulent) in under 100 ms.
- **Explainable Decisions** — Every model output generates local SHAP explanation vectors pinned to IPFS, with their content identifiers anchored on-chain.
- **Immutable Audit Trail** — Hyperledger Fabric records all governance actions and regulatory submissions across channels (`modelgovernance`, `frauddetection`, `compliance`, `regulatory`).
- **Policy Engine Thresholds** — Integrated policy checks block models automatically if they fail minimum requirements (e.g. testing thresholds: AUC-ROC $\ge$ 0.80, F1 $\ge$ 0.55).
- **Multi-Role RBAC Dashboard** — Personalized interfaces for 6 actor profiles (Data Scientist, ML Engineer, Fraud Analyst, Internal Auditor, External Auditor, Regulator).
- **Direct Regulatory Node** — The Regulator participates directly in the network, querying the compliance channel without bank intermediation.

---

## 💻 System Architecture

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
│  Peer Regulator  │  Gateway (Go)    │  MySQL (Dockerized)   │
│  CouchDB x3      │  Drift Monitor   │  IPFS / CouchDB       │
└──────────────────┴──────────────────┴───────────────────────┘
```

---

## ⚙️ Prerequisites & Dependencies

To deploy and run BlockML-Gov, you will need:

### System Requirements
* **OS**: Linux (Ubuntu 22.04 LTS or 24.04 LTS) or Windows 10/11 with WSL2.
* **RAM**: 8 GB minimum (16 GB recommended).
* **Storage**: 25 GB free disk space.

### Dependencies & Versions
* **Docker Engine** v24.x+ & **Docker Compose** v2.x+
* **Hyperledger Fabric** v2.5.0 & **Fabric-CA** v1.5.5
* **Python** v3.11+
* **Git** v2.x+

---

## 🚀 Installation & Deployment

> [!NOTE]
> For a detailed, step-by-step walkthrough of the environment setup and network initialization, please refer to the [Installation Guide (GUIDE_INSTALLATION.md)](./GUIDE_INSTALLATION.md).

Follow these steps to deploy the entire stack (Hyperledger Fabric network + application services):

### 1. Clone the Project & Prepare Fabric Binaries
Clone the repository and ensure you have `fabric-samples` installed in your home directory:
```bash
cd ~
git clone -b blockmlgov https://github.com/OurraiAsmae/projet_pfa_2026.git fraud-governance-system
cd fraud-governance-system
```
*If you do not have Hyperledger Fabric v2.5.0 binaries installed locally, run:*
```bash
cd ~
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0 1.5.5
```

### 2. Configure Symbol Link & Local Hosts
Set up the link to the Fabric binaries and register the DNS descriptors in `/etc/hosts` so your local system can reach the Fabric docker nodes:
```bash
# Link fabric-samples
cd ~/fraud-governance-system
rm -rf fabric-samples
ln -s ~/fabric-samples fabric-samples

# Append hosts config
sudo bash -c 'cat >> /etc/hosts << HOSTS
127.0.0.1  orderer.fraud-governance.com
127.0.0.1  peer0.bank.fraud-governance.com
127.0.0.1  peer0.audit.fraud-governance.com
127.0.0.1  peer0.regulator.fraud-governance.com
HOSTS'
```

### 3. Launch the Stack
Execute the automatic startup script. This script boots the Fabric network (peers, CouchDB databases, orderer), sets up channels, compiles/deploys the smart contracts, and boots the microservices stack (MySQL, Redis, RabbitMQ, Gateway, API, MLflow, and Dashboard):
```bash
chmod +x start-blockmlgov.sh
./start-blockmlgov.sh
```

---

## 🖥️ Port Mapping & Access URLs

Once all containers show `Up`, you can access the following services:

| Component | URL | Default Credentials |
|---|---|---|
| **Streamlit Dashboard** | [http://localhost:8501](http://localhost:8501) | *See Test Accounts below* |
| **API Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | — |
| **MLflow Registry** | [http://localhost:5000](http://localhost:5000) | — |
| **RabbitMQ Management** | [http://localhost:15672](http://localhost:15672) | `guest` / `guest` |
| **MySQL Database Port** | `33066` | `blockmlgov` / `blockmlgov` |

---

## 👤 Test Accounts (RBAC)

Use these credentials to log into the Streamlit dashboard:

| Username | Password | Role | Department |
|---|---|---|---|
| `admin` | `Admin@2026!` | Administrator | IT Administration |
| `data.scientist1` | `Ds@2026!` | Data Scientist | AI & ML |
| `ml.engineer1` | `Mle@2026!` | ML Engineer | MLOps Engineering |
| `compliance.officer1` | `Co@2026!` | Compliance Officer | Risk & Compliance |
| `internal.auditor1` | `Ia@2026!` | Internal Auditor | Internal Audit |
| `regulator1` | `Reg@2026!` | Regulator | BAM Morocco |

---

## 🧪 Usage Example (Step-by-Step Scenario)

Here is a quick workflow demonstrating the Model Governance lifecycle:

### Step 1: Submit a Model (Data Scientist)
1. Log in to the dashboard as **Data Scientist** (`data.scientist1`).
2. Go to **Model Registration**.
3. Upload a model pickle file (e.g. `mlops/models/random_forest.pkl`).
4. Select the dataset **`DS-transactions_bancaires-v1`** and submit.
5. The platform automatically evaluates the metrics, registers the model run in MLflow, tests compatibility with Policy PR-005, generates a Model Card, pins it to IPFS, and submits it to the blockchain ledger as `SUBMITTED`.

### Step 2: Regulatory Validation (Compliance Officer)
1. Log in as **Compliance Officer** (`compliance.officer1`).
2. Go to **Compliance Validation**.
3. Select the submitted model, review the metrics against BAM thresholds, and click **Validate Compliance**. The ledger state updates to `COMPLIANCE_VALIDATED`.

### Step 3: Technical Verification (ML Engineer)
1. Log in as **ML Engineer** (`ml.engineer1`).
2. Go to **Technical Approval**.
3. Run the performance test (verifying inference latency < 100 ms) and check integrity against the MLflow model hash.
4. Click **Approve Technically**. The model is now registered as `APPROVED` and ready for production deployment.

---

## 📄 License

This software is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for the full license text.

---

## 👥 Contributors

* **Asmae Ourrai** — ML Pipeline integration, API backend, and end-to-end system orchestration.
* **Safae El Ouajidi** — Blockchain architecture, Hyperledger Fabric channels, and cross-environment deployment reliability.
* **Marwa M'haya** — ML model development, training, and evaluation.
