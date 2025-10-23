-- Base schema for InboxBrain (MySQL 8)
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS emails_raw (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  provider VARCHAR(64) NOT NULL,
  mailbox  VARCHAR(190) NOT NULL,
  message_id VARCHAR(255) NULL,
  uid BIGINT NULL,
  from_address VARCHAR(255) NULL,
  subject TEXT NULL,
  body_text MEDIUMTEXT NULL,
  body_html MEDIUMTEXT NULL,
  received_at DATETIME NULL,
  hash_dedupe CHAR(64) NULL,

  -- generated normalized columns for unique key
  message_id_norm VARCHAR(255) AS (IFNULL(message_id,'')) STORED,
  external_id_norm VARCHAR(255) AS (IFNULL('', '')) STORED, -- placeholder if you ingest from APIs that provide external ids
  uid_norm BIGINT AS (IFNULL(uid,0)) STORED,

  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE KEY uniq_msg (provider, mailbox, message_id_norm, external_id_norm, uid_norm),
  KEY idx_received (received_at),
  KEY idx_hash (hash_dedupe)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS email_queue (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email_id BIGINT NOT NULL,
  status ENUM('pending','processing','done','error') NOT NULL DEFAULT 'pending',
  attempts INT NOT NULL DEFAULT 0,
  error_msg TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_status (status),
  KEY idx_email (email_id),
  CONSTRAINT fk_queue_email FOREIGN KEY (email_id) REFERENCES emails_raw(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS email_ai (
  email_id BIGINT PRIMARY KEY,
  intent VARCHAR(64) NULL,
  confidence DECIMAL(5,4) NULL,
  priority VARCHAR(32) NULL,
  entities JSON NULL,
  model VARCHAR(128) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ai_email FOREIGN KEY (email_id) REFERENCES emails_raw(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS runs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  provider VARCHAR(64) NOT NULL,
  mailbox  VARCHAR(190) NOT NULL,
  checkpoint_type VARCHAR(64) NOT NULL,
  checkpoint_value VARCHAR(255) NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_checkpoint (provider, mailbox, checkpoint_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS settings (
  `key` VARCHAR(190) PRIMARY KEY,
  `value` TEXT,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
