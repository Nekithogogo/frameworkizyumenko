-- ==========================================
-- CertHub: структура базы данных
-- ==========================================

-- Организации — владельцы доменов и заказчики сертификатов
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    inn TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL
);

-- Домены; каждый принадлежит одной организации
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    organization_id INTEGER NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

-- SSL-сертификаты; срок действия хранится датами ГГГГ-ММ-ДД,
-- признак отзыва — числом 0/1
CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY,
    serial_number TEXT NOT NULL UNIQUE,
    cert_type TEXT NOT NULL CHECK (cert_type IN ('DV', 'OV', 'EV')),
    domain_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    is_revoked INTEGER NOT NULL DEFAULT 0,
    CHECK (valid_to > valid_from),
    FOREIGN KEY (domain_id) REFERENCES domains(id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);
