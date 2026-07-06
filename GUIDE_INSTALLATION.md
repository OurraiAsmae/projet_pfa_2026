# 📘 Guide d'Installation et de Test — BlockML-Gov v4.0

> **Plateforme de Gouvernance IA pour le Secteur Bancaire**  
> Hyperledger Fabric 2.5 · FastAPI · Streamlit · MLflow · RabbitMQ · Redis · MySQL (Dockerisé)  
> *Asmae Ourrai · Safae El Ouajidi · Marwa M'haya*

Ce guide documente le déploiement **entièrement automatisé et corrigé** du projet. Contrairement aux versions précédentes, **l'authentification MySQL est désormais intégrée à la stack Docker**, éliminant le besoin d'installer WAMP Server ou MySQL localement sur l'hôte Windows.

---

## ⚙️ Prérequis Système

| Outil | Version minimale | Notes / Commande de vérification |
|---|---|---|
| **OS** | Ubuntu 22.04 / 24.04 LTS | WSL2 recommandé pour Windows |
| **Docker** | 24.x+ | `docker --version` |
| **Docker Compose** | 2.x+ (plugin) | `docker compose version` |
| **Git** | 2.x+ | `git --version` |
| **RAM disponible** | **8 Go** (16 Go recommandés) | `free -h` |
| **Espace disque libre**| **25 Go** | `df -h` |

---

## 📥 1. Préparation de l'Environnement

### 1.1 Cloner le Projet et Vérifier les Binaires Fabric

Clonez le dépôt Git dans votre répertoire utilisateur sous WSL ou Linux :

```bash
cd ~
git clone https://github.com/elouajidisafae/BlockMLGov.git fraud-governance-system
cd fraud-governance-system
```

Assurez-vous que le dossier `fabric-samples` contenant les binaires d'Hyperledger Fabric v2.5.0 est présent dans votre répertoire personnel (`~/fabric-samples`).
Si ce n'est pas le cas, installez Fabric v2.5.0 et Fabric-CA v1.5.5 :

```bash
cd ~
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0 1.5.5
```

### 1.2 Configuration du Lien Symbolique (Corrigé)

Le projet nécessite un lien symbolique vers `fabric-samples`. Pour éviter les dossiers imbriqués, exécutez la commande de nettoyage et de création suivante :

```bash
cd ~/fraud-governance-system
rm -rf fabric-samples
ln -s ~/fabric-samples fabric-samples
```

Vérifiez que le lien pointe correctement vers le répertoire d'origine :
```bash
ls -la | grep fabric-samples
# Attendu : fabric-samples -> /home/fabric/fabric-samples
```

---

## 🌐 2. Configuration Réseau & DNS

### 2.1 Configuration de /etc/hosts (Hôte)

Le client Fabric sur la machine hôte doit pouvoir résoudre les adresses des conteneurs Fabric.
Exécutez cette commande dans votre terminal Linux (mot de passe root requis) :

```bash
sudo bash -c 'cat >> /etc/hosts << HOSTS
127.0.0.1  orderer.fraud-governance.com
127.0.0.1  peer0.bank.fraud-governance.com
127.0.0.1  peer0.audit.fraud-governance.com
127.0.0.1  peer0.regulator.fraud-governance.com
HOSTS'
```

### 2.2 DNS de Résolution WSL

Assurez-vous que WSL dispose d'une configuration DNS valide pour télécharger les images Docker en exécutant (si nécessaire) :
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

---

## 🚀 3. Démarrage de la Stack Applicative

Démarrez le script d'initialisation automatique. Ce script va :
1. Lancer le réseau Hyperledger Fabric (Orderer, Peers Bank/Audit/Regulator et leurs bases CouchDB).
2. Lancer la stack applicative (Redis, MySQL Dockerisé pré-initialisé avec les schémas et utilisateurs, FastAPI, Streamlit Dashboard, Gateway Go, RabbitMQ, MLflow, Redis Commander).
3. Configurer automatiquement les canaux Fabric (`modelgovernance`, `frauddetection`, `compliance`, `regulatory`), installer, approuver et commiter les chaincodes associés.

```bash
chmod +x start-blockmlgov.sh
./start-blockmlgov.sh
```

*(Note : Lors du premier démarrage, le téléchargement et la compilation des modules peuvent prendre 10 à 15 minutes. Les lancements suivants seront instantanés).*

---

## 🖥️ 4. URLs des Services & Accès

Une fois le démarrage complété avec succès, tous les services sont disponibles aux adresses suivantes :

| Service / Interface | URL d'accès | Identifiants par défaut |
|---|---|---|
| **Dashboard Principal** | [http://localhost:8501](http://localhost:8501) | *Voir comptes ci-dessous* |
| **Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | — |
| **Interface Auth API** | [http://localhost:8001/docs](http://localhost:8001/docs) | — |
| **MLflow Server** | [http://localhost:5000](http://localhost:5000) | — |
| **Redis Commander** | [http://localhost:8081](http://localhost:8081) | — |
| **RabbitMQ Management**| [http://localhost:15672](http://localhost:15672) | `guest` / `guest` |
| **CouchDB Fauxton** | [http://localhost:5984/_utils](http://localhost:5984/_utils) | `admin` / `adminpw` |

---

## 👤 5. Comptes de Test du Dashboard

Le conteneur MySQL (`blockmlgov-mysql`) est pré-rempli avec les comptes suivants. Vous pouvez utiliser n'importe lequel d'entre eux pour tester le contrôle d'accès basé sur les rôles (RBAC) sur le dashboard Streamlit.

### Option 1 — Identifiants standards (Recommandés)

| Nom d'utilisateur | Mot de passe | Rôle associé | Département |
|---|---|---|---|
| `admin` | `Admin@2026!` | Administrateur | IT Administration |
| `data.scientist1` | `Ds@2026!` | Data Scientist | AI & ML |
| `ml.engineer1` | `Mle@2026!` | ML Engineer | MLOps Engineering |
| `fraud.analyst1` | `Fa@2026!` | Fraud Analyst | Fraud Detection |
| `compliance.officer1` | `Co@2026!` | Compliance Officer | Risk & Compliance |
| `internal.auditor1` | `Ia@2026!` | Internal Auditor | Internal Audit |
| `external.auditor1` | `Ea@2026!` | External Auditor | External Audit |
| `regulator1` | `Reg@2026!` | Regulator | BAM Morocco |

### Option 2 — Identifiants v4 alternatifs

| Nom d'utilisateur | Mot de passe | Rôle associé |
|---|---|---|
| `admin_v4` | `Admin@BlockML2026!` | Administrateur |
| `data.scientist1_v4` | `DS@BlockML2026!` | Data Scientist |
| `ml.engineer1_v4` | `MLE@BlockML2026!` | ML Engineer |
| `fraud.analyst1_v4` | `FA@BlockML2026!` | Fraud Analyst |
| `compliance1` | `CO@BlockML2026!` | Compliance Officer |
| `auditor1` | `AUD@BlockML2026!` | Internal Auditor |
| `ext.auditor1` | `EXT@BlockML2026!` | External Auditor |
| `regulator1_v4` | `REG@BlockML2026!` | Regulator |

---

## 🧪 6. Scénarios de Test Applicatifs

### 🔹 Scénario 1 — Cycle de Gouvernance d'un Modèle
1. Connectez-vous avec le rôle **Data Scientist** (`data.scientist1`).
2. Accédez à l'onglet **Upload Model** pour enregistrer et versionner un nouveau modèle ML.
3. Déconnectez-vous et connectez-vous avec le rôle **ML Engineer** (`ml.engineer1`).
4. Accédez à l'onglet **Technical Approval** pour voir le modèle soumis, examiner son rapport d'évaluation et valider ou rejeter sa mise en production.
5. Accédez à l'onglet **Model Deployment** pour pousser le modèle approuvé vers la production.

### 🔹 Scénario 2 — Détection de Fraude et Alertes en Direct
1. Connectez-vous avec le rôle **Fraud Analyst** (`fraud.analyst1`).
2. Accédez à la page **Live Dashboard** pour observer en temps réel les flux de transactions financières et les scores de suspicion générés par le modèle.
3. Accédez à la page **Alerts** pour gérer les files d'attente d'alertes transmises via RabbitMQ.

### 🔹 Scénario 3 — Piste d'Audit Immuable (Audit Trail)
1. Connectez-vous avec le rôle **Internal Auditor** (`internal.auditor1`) ou **External Auditor** (`external.auditor1`).
2. Accédez à la page **Audit Trail** pour interroger directement le registre partagé et immuable d'Hyperledger Fabric et vérifier l'intégrité de toutes les transactions et décisions enregistrées.

---

## 🔧 7. Dépannage

### Erreur de port 3306 déjà utilisé sur l'hôte
Le port MySQL standard (`3306`) peut être utilisé par un service local (WAMP, MySQL local, etc.).
Le conteneur MySQL (`blockmlgov-mysql`) a été configuré pour exposer le port **`33066`** sur la machine hôte. Vos services internes communiquent sur le port interne `3306` via le réseau virtuel Docker, ce qui élimine les conflits. Si vous utilisez un client de base de données externe (comme DBeaver), connectez-vous au port **`33066`**.

### `caching_sha2_password` non supporté par l'API d'authentification
Si l'auth-service affiche une erreur concernant le protocole d'authentification de la base de données :
Le conteneur `auth-service` est construit avec le module Python `cryptography` pré-installé, résolvant nativement ce problème. Assurez-vous d'avoir reconstruit la stack (`docker compose up --build`).

### Problème de résolution DNS dans WSL
Si Docker ne parvient pas à télécharger les images (erreurs de timeout DNS) :
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Tout arrêter et réinitialiser proprement
Pour arrêter proprement tous les conteneurs et nettoyer les réseaux et volumes :
```bash
docker compose down
cd blockchain/network
docker compose -f docker-compose-fabric.yml down
docker network rm fraud-governance-net
```

---

*BlockML-Gov v4.0*
