-- MySQL schema for the plant app (apply manually or via your migration tool).
-- No credentials are stored here; connection details come from environment variables.
-- Requires MySQL 8.0+.

CREATE DATABASE IF NOT EXISTS farm_demo
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE farm_demo;

CREATE TABLE IF NOT EXISTS Crops (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    crop_name     VARCHAR(120) NOT NULL,
    field_name    VARCHAR(120),
    quantity      DECIMAL(12, 3),
    planting_date DATE,
    harvest_date  DATE,
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_crop_name (crop_name)
) ENGINE = InnoDB;

DELIMITER $$
DROP PROCEDURE IF EXISTS InsertCrop $$
CREATE PROCEDURE InsertCrop (
    IN p_crop_name     VARCHAR(120),
    IN p_field_name    VARCHAR(120),
    IN p_quantity      DECIMAL(12, 3),
    IN p_planting_date DATE,
    IN p_harvest_date  DATE,
    IN p_notes         TEXT
)
BEGIN
    INSERT INTO Crops (crop_name, field_name, quantity, planting_date, harvest_date, notes)
    VALUES (p_crop_name, p_field_name, p_quantity, p_planting_date, p_harvest_date, p_notes);
END $$
DELIMITER ;
