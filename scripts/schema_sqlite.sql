-- SQLite demonstration schema (created automatically in sqlite DB_MODE).
CREATE TABLE IF NOT EXISTS crops (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name     TEXT NOT NULL,
    field_name    TEXT,
    quantity      REAL,
    planting_date TEXT,
    harvest_date  TEXT,
    notes         TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_crops_name ON crops (crop_name);
