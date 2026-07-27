CREATE DATABASE IF NOT EXISTS blockmlgov_auth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE blockmlgov_auth;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('Admin','Data Scientist','Compliance Officer','ML Engineer',
            'Fraud Analyst','Internal Auditor','External Auditor','Regulator') NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  department VARCHAR(100) NOT NULL,
  is_active TINYINT(1) DEFAULT 1,
  failed_attempts INT DEFAULT 0,
  locked_until DATETIME DEFAULT NULL,
  last_login DATETIME DEFAULT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(50) DEFAULT 'system',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY username (username),
  UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token VARCHAR(512) NOT NULL,
  refresh_token VARCHAR(512) DEFAULT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  ip_address VARCHAR(50) DEFAULT NULL,
  is_active TINYINT(1) DEFAULT 1,
  UNIQUE KEY token (token),
  UNIQUE KEY refresh_token (refresh_token),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT DEFAULT NULL,
  username VARCHAR(50) DEFAULT NULL,
  action VARCHAR(100) NOT NULL,
  details TEXT,
  ip_address VARCHAR(50) DEFAULT NULL,
  success TINYINT(1) DEFAULT 1,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert user accounts (from the user's guide)
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('admin', '$2b$12$GA3HeZyRsFgMgIJJTCaQ.OgISbcqQOL7zxgqEi8AOZ9jXIIHiraeq', 'Admin', 'Admin', 'IT Administration', 'admin@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$GA3HeZyRsFgMgIJJTCaQ.OgISbcqQOL7zxgqEi8AOZ9jXIIHiraeq';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('data.scientist1', '$2b$12$86JlpYMxC11Mrh1GVeM5.uaPWxjiQkGyH9DUOuQ62Ofd8ljCyAXmm', 'Data Scientist', 'Data Scientist 1', 'AI & ML', 'ds1@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$86JlpYMxC11Mrh1GVeM5.uaPWxjiQkGyH9DUOuQ62Ofd8ljCyAXmm';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('compliance.officer1', '$2b$12$Dfj5/Q8qqi6QqS6j50slKujy0VNtvgqa3ri0cFxz7sYhrI0M2SsRu', 'Compliance Officer', 'Compliance Off. 1', 'Risk & Compliance', 'co1@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$Dfj5/Q8qqi6QqS6j50slKujy0VNtvgqa3ri0cFxz7sYhrI0M2SsRu';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('ml.engineer1', '$2b$12$Vu5Qs4wyfKfgFD5eKNCvLe5z.GlllCWxFEM2ZDglXFRxqGI7t8826', 'ML Engineer', 'ML Engineer 1', 'MLOps Engineering', 'mle1@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$Vu5Qs4wyfKfgFD5eKNCvLe5z.GlllCWxFEM2ZDglXFRxqGI7t8826';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('fraud.analyst1', '$2b$12$28YPJ7TXV8yFOyvct/HaF.iayoKdcPBzeK8gCdFfYnlqdkVQ2cABS', 'Fraud Analyst', 'Fraud Analyst 1', 'Fraud Detection', 'fa1@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$28YPJ7TXV8yFOyvct/HaF.iayoKdcPBzeK8gCdFfYnlqdkVQ2cABS';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('internal.auditor1', '$2b$12$pTBgjht/oszFGdN8w7aKF.6.CKrQK7zBXFxzV6CtbTw.ZX2Nklpvm', 'Internal Auditor', 'Internal Aud. 1', 'Internal Audit', 'ia1@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$pTBgjht/oszFGdN8w7aKF.6.CKrQK7zBXFxzV6CtbTw.ZX2Nklpvm';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('external.auditor1', '$2b$12$pV0Z0Q2gxOocS8ha.hMtXOATB6gylmGqAapukCMuKb7X0FMXty5g6', 'External Auditor', 'External Aud. 1', 'External Audit', 'ea1@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$pV0Z0Q2gxOocS8ha.hMtXOATB6gylmGqAapukCMuKb7X0FMXty5g6';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('regulator1', '$2b$12$ew/hCaoJ9CGOOsxBYEeTROxjCVjPG9naRulr8C7MeOR77GKX110Wq', 'Regulator', 'Regulator 1', 'BAM Morocco', 'reg1@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$ew/hCaoJ9CGOOsxBYEeTROxjCVjPG9naRulr8C7MeOR77GKX110Wq';

-- Insert user accounts (from the original GUIDE_INSTALLATION.md with _v4 suffix or direct matching usernames)
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('data.scientist1_v4', '$2b$12$zE9Fi0.gtZm.R6eNMNg2te0S3GnXMsS9FGk8zLu/uSPIlPBS.O7MK', 'Data Scientist', 'Data Scientist v4', 'AI & ML', 'ds_v4@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$zE9Fi0.gtZm.R6eNMNg2te0S3GnXMsS9FGk8zLu/uSPIlPBS.O7MK';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('ml.engineer1_v4', '$2b$12$FkBjvOFBq/7wXJPPXGg95uI.tSbAS2XubePLEsOFTh5HhWAcQ8M/O', 'ML Engineer', 'ML Engineer v4', 'MLOps Engineering', 'mle_v4@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$FkBjvOFBq/7wXJPPXGg95uI.tSbAS2XubePLEsOFTh5HhWAcQ8M/O';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('fraud.analyst1_v4', '$2b$12$f/hM9YqOGQ5RGCK4ftXOfe1AWRtl.MpMiYeUgE3MAtKaak4m.fxEi', 'Fraud Analyst', 'Fraud Analyst v4', 'Fraud Detection', 'fa_v4@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$f/hM9YqOGQ5RGCK4ftXOfe1AWRtl.MpMiYeUgE3MAtKaak4m.fxEi';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('compliance1', '$2b$12$pD.fbjj3n1gRcpRf0A6rSOPsOcZy8bhBja12ew4vmZB3vykgIfyx6', 'Compliance Officer', 'Compliance Off. 2', 'Risk & Compliance', 'co2@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$pD.fbjj3n1gRcpRf0A6rSOPsOcZy8bhBja12ew4vmZB3vykgIfyx6';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('auditor1', '$2b$12$OYLsnk2hbzPrh4PpMStnU.Z9H8d8CgUlMVomkNxEnCIWC95n5GvRW', 'Internal Auditor', 'Internal Aud. 2', 'Internal Audit', 'ia2@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$OYLsnk2hbzPrh4PpMStnU.Z9H8d8CgUlMVomkNxEnCIWC95n5GvRW';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('ext.auditor1', '$2b$12$aH0.CnAuRbe.sW8ACvJgTO7tzsMMp9s5sB3Hr51Rj59TjR1gv1Hu2', 'External Auditor', 'External Aud. 2', 'External Audit', 'ea2@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$aH0.CnAuRbe.sW8ACvJgTO7tzsMMp9s5sB3Hr51Rj59TjR1gv1Hu2';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('regulator1_v4', '$2b$12$MvIi.1XiilkHevmU6yQhGO4QL7RgsV9GuiBa0rEqEGPIt0RqzG9Sm', 'Regulator', 'Regulator v4', 'BAM Morocco', 'reg_v4@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$MvIi.1XiilkHevmU6yQhGO4QL7RgsV9GuiBa0rEqEGPIt0RqzG9Sm';
INSERT INTO users (username, password_hash, role, full_name, department, email) VALUES ('admin_v4', '$2b$12$7uzES6V7PvJdG4L1CbpT5eTBtahe5fImhR0sCVwYg7EUYnjixvEU2', 'Admin', 'Admin v4', 'IT Administration', 'admin_v4@blockmlgov.ma') ON DUPLICATE KEY UPDATE password_hash='$2b$12$7uzES6V7PvJdG4L1CbpT5eTBtahe5fImhR0sCVwYg7EUYnjixvEU2';
