-- Schema for InboxBrain (MySQL 8+)

CREATE TABLE IF NOT EXISTS email_categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL UNIQUE,
  description VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS emails_raw (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  provider VARCHAR(32) NOT NULL,
  mailbox  VARCHAR(128) NOT NULL,

  -- chiavi "grezze" che possono essere NULL
  message_id VARCHAR(255) NULL,
  uid BIGINT NULL,
  external_id VARCHAR(255) NULL,

  from_address VARCHAR(255) NOT NULL,
  from_name VARCHAR(255) NULL,
  to_addresses JSON NULL,
  cc_addresses JSON NULL,
  subject VARCHAR(500) NULL,
  snippet VARCHAR(500) NULL,
  body_text MEDIUMTEXT NULL,
  body_html MEDIUMTEXT NULL,
  has_attachments TINYINT(1) DEFAULT 0,
  received_at DATETIME(6) NOT NULL,
  hash_dedupe CHAR(64) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- 🔧 colonne generate per normalizzare i NULL (servono per l'indice unico)
  message_id_norm VARCHAR(255) AS (IFNULL(message_id, '')) STORED,
  external_id_norm VARCHAR(255) AS (IFNULL(external_id, '')) STORED,
  uid_norm BIGINT AS (IFNULL(uid, 0)) STORED,

  -- indici
  UNIQUE KEY uniq_msg (provider, mailbox, message_id_norm, external_id_norm, uid_norm),
  KEY idx_received (received_at),
  KEY idx_hash (hash_dedupe)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS email_queue (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email_id BIGINT NOT NULL,
  status ENUM('pending','processing','done','error') DEFAULT 'pending',
  attempts INT DEFAULT 0,
  locked_at DATETIME NULL,
  error_msg VARCHAR(1000) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_email (email_id),
  CONSTRAINT fk_q_email FOREIGN KEY (email_id) REFERENCES emails_raw(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS email_ai (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email_id BIGINT NOT NULL,
  model_name VARCHAR(128),
  intent VARCHAR(64) NOT NULL,
  confidence DECIMAL(5,4) NULL,
  category_id INT NULL,
  extracted_json JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_ai_email (email_id),
  CONSTRAINT fk_ai_email FOREIGN KEY (email_id) REFERENCES emails_raw(id) ON DELETE CASCADE,
  CONSTRAINT fk_ai_cat FOREIGN KEY (category_id) REFERENCES email_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS runs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  provider VARCHAR(32) NOT NULL,
  mailbox  VARCHAR(128) NOT NULL,
  checkpoint_type ENUM('imap_uid','gmail_history_id','custom') NOT NULL,
  checkpoint_value VARCHAR(255) NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_run (provider, mailbox, checkpoint_type)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS email_attachments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email_id BIGINT NOT NULL,
  filename VARCHAR(255),
  content_type VARCHAR(255),
  size_bytes BIGINT,
  storage_uri VARCHAR(1024),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_att_email (email_id),
  CONSTRAINT fk_att_email FOREIGN KEY (email_id) REFERENCES emails_raw(id) ON DELETE CASCADE
) ENGINE=InnoDB;
