-- ==========================================
-- CertHub: SQL-запросы проекта
-- ==========================================
--
-- Каждый запрос начинается строкой «-- name: <имя>»: по этому имени
-- запрос загружает модуль db/queries.py и выполняют Django-представления.
-- Значения передаются именованными параметрами (:today, :id, ...),
-- а не подстановкой строк в текст запроса.
--
-- Проверка в SQLite CLI (из корня проекта):
--   sqlite3 data/certhub.sqlite
--   .parameter set :today "'2026-10-25'"
--   .parameter set :date "'2026-10-25'"
--   .parameter set :id 3
--   .parameter set :days 30
--   .parameter set :min_domains 2
--   .read sql/queries.sql
--
-- Статус сертификата на дату :today вычисляется выражением CASE:
-- revoked — отозван, pending — еще не действует, expired — истек,
-- expiring — до окончания не больше 30 дней, active — действует.


-- name: summary
-- 1. Сводка для главной страницы: количество организаций, доменов,
--    сертификатов и средний срок действия (агрегатные функции)
SELECT
    (SELECT COUNT(*) FROM organizations) AS organizations_count,
    (SELECT COUNT(*) FROM domains) AS domains_count,
    COUNT(*) AS certificates_count,
    SUM(is_revoked) AS revoked_count,
    ROUND(AVG(julianday(valid_to) - julianday(valid_from))) AS avg_days
FROM certificates;


-- name: domain_list
-- 2. Список доменов с владельцем, числом сертификатов и датой, до которой
--    домен защищен на :today (JOIN, LEFT JOIN, GROUP BY)
SELECT
    d.id,
    d.name,
    o.name AS organization_name,
    COUNT(c.id) AS certificates_count,
    MAX(
        CASE
            WHEN c.is_revoked = 0
                AND :today BETWEEN c.valid_from AND c.valid_to
            THEN c.valid_to
        END
    ) AS protected_until
FROM domains AS d
JOIN organizations AS o
    ON o.id = d.organization_id
LEFT JOIN certificates AS c
    ON c.domain_id = d.id
GROUP BY d.id, d.name, o.name
ORDER BY d.name;


-- name: domain_detail
-- 3. Один домен с владельцем и защитой на :today (JOIN, WHERE по :id)
SELECT
    d.id,
    d.name,
    o.name AS organization_name,
    o.inn,
    o.email,
    COUNT(c.id) AS certificates_count,
    MAX(
        CASE
            WHEN c.is_revoked = 0
                AND :today BETWEEN c.valid_from AND c.valid_to
            THEN c.valid_to
        END
    ) AS protected_until
FROM domains AS d
JOIN organizations AS o
    ON o.id = d.organization_id
LEFT JOIN certificates AS c
    ON c.domain_id = d.id
WHERE d.id = :id
GROUP BY d.id, d.name, o.name, o.inn, o.email;


-- name: domain_certificates
-- 4. История сертификатов домена со статусом на :today (WHERE по :id)
SELECT
    c.id,
    c.serial_number,
    c.cert_type,
    c.valid_from,
    c.valid_to,
    CASE
        WHEN c.is_revoked = 1 THEN 'revoked'
        WHEN :today < c.valid_from THEN 'pending'
        WHEN :today > c.valid_to THEN 'expired'
        WHEN julianday(c.valid_to) - julianday(:today) <= 30 THEN 'expiring'
        ELSE 'active'
    END AS status
FROM certificates AS c
WHERE c.domain_id = :id
ORDER BY c.valid_to;


-- name: unprotected_domains
-- 5. Домены без действующего сертификата на выбранную дату :date
--    (WHERE, подзапрос NOT IN, JOIN)
SELECT
    d.id,
    d.name,
    o.name AS organization_name,
    o.email
FROM domains AS d
JOIN organizations AS o
    ON o.id = d.organization_id
WHERE d.id NOT IN (
    SELECT c.domain_id
    FROM certificates AS c
    WHERE c.is_revoked = 0
        AND :date BETWEEN c.valid_from AND c.valid_to
)
ORDER BY d.name;


-- name: certificate_list
-- 6. Список сертификатов с доменом, организацией, остатком дней и статусом
--    на :today, упорядоченный по дате окончания (JOIN трех таблиц)
SELECT
    c.id,
    c.serial_number,
    c.cert_type,
    d.id AS domain_id,
    d.name AS domain_name,
    o.name AS organization_name,
    c.valid_from,
    c.valid_to,
    CAST(julianday(c.valid_to) - julianday(:today) AS INTEGER) AS days_left,
    CASE
        WHEN c.is_revoked = 1 THEN 'revoked'
        WHEN :today < c.valid_from THEN 'pending'
        WHEN :today > c.valid_to THEN 'expired'
        WHEN julianday(c.valid_to) - julianday(:today) <= 30 THEN 'expiring'
        ELSE 'active'
    END AS status
FROM certificates AS c
JOIN domains AS d
    ON d.id = c.domain_id
JOIN organizations AS o
    ON o.id = c.organization_id
ORDER BY c.valid_to;


-- name: certificate_detail
-- 7. Полная информация об одном сертификате (JOIN, WHERE по :id)
SELECT
    c.id,
    c.serial_number,
    c.cert_type,
    c.is_revoked,
    d.id AS domain_id,
    d.name AS domain_name,
    o.name AS organization_name,
    o.inn,
    o.email,
    c.valid_from,
    c.valid_to,
    CAST(julianday(c.valid_to) - julianday(c.valid_from) AS INTEGER)
        AS days_total,
    CAST(julianday(c.valid_to) - julianday(:today) AS INTEGER) AS days_left,
    CASE
        WHEN c.is_revoked = 1 THEN 'revoked'
        WHEN :today < c.valid_from THEN 'pending'
        WHEN :today > c.valid_to THEN 'expired'
        WHEN julianday(c.valid_to) - julianday(:today) <= 30 THEN 'expiring'
        ELSE 'active'
    END AS status
FROM certificates AS c
JOIN domains AS d
    ON d.id = c.domain_id
JOIN organizations AS o
    ON o.id = c.organization_id
WHERE c.id = :id;


-- name: expiring_certificates
-- 8. Неотозванные сертификаты, срок которых закончится в ближайшие
--    :days дней начиная с :today (WHERE, BETWEEN, JOIN)
SELECT
    c.id,
    c.serial_number,
    c.cert_type,
    d.id AS domain_id,
    d.name AS domain_name,
    o.name AS organization_name,
    o.email,
    c.valid_to,
    CAST(julianday(c.valid_to) - julianday(:today) AS INTEGER) AS days_left
FROM certificates AS c
JOIN domains AS d
    ON d.id = c.domain_id
JOIN organizations AS o
    ON o.id = c.organization_id
WHERE c.is_revoked = 0
    AND c.valid_to BETWEEN :today AND date(:today, '+' || :days || ' days')
ORDER BY c.valid_to;


-- name: status_counts
-- 9. Количество сертификатов в каждом статусе на :today
--    (агрегатная функция COUNT, GROUP BY по вычисляемому полю)
SELECT
    CASE
        WHEN c.is_revoked = 1 THEN 'revoked'
        WHEN :today < c.valid_from THEN 'pending'
        WHEN :today > c.valid_to THEN 'expired'
        WHEN julianday(c.valid_to) - julianday(:today) <= 30 THEN 'expiring'
        ELSE 'active'
    END AS status,
    COUNT(*) AS certificates_count
FROM certificates AS c
GROUP BY status
ORDER BY certificates_count DESC, status;


-- name: type_statistics
-- 10. Статистика по типам сертификатов: количество, средний,
--     минимальный и максимальный срок (COUNT, AVG, MIN, MAX, GROUP BY)
SELECT
    cert_type,
    COUNT(*) AS certificates_count,
    ROUND(AVG(julianday(valid_to) - julianday(valid_from))) AS avg_days,
    MIN(valid_from) AS first_issued,
    MAX(valid_to) AS last_valid_to
FROM certificates
GROUP BY cert_type
ORDER BY cert_type;


-- name: organization_statistics
-- 11. Организации: количество доменов, сертификатов и действующих на
--     :today сертификатов, включая организации без сертификатов
--     (LEFT JOIN, COUNT, SUM, GROUP BY)
SELECT
    o.id,
    o.name,
    o.inn,
    COUNT(DISTINCT d.id) AS domains_count,
    COUNT(c.id) AS certificates_count,
    COALESCE(
        SUM(
            CASE
                WHEN c.is_revoked = 0
                    AND :today BETWEEN c.valid_from AND c.valid_to
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS valid_count
FROM organizations AS o
LEFT JOIN domains AS d
    ON d.organization_id = o.id
LEFT JOIN certificates AS c
    ON c.domain_id = d.id
GROUP BY o.id, o.name, o.inn
ORDER BY domains_count DESC, o.name;


-- name: large_organizations
-- 12. Организации, у которых не меньше :min_domains доменов
--     (JOIN, GROUP BY, фильтрация групп HAVING)
SELECT
    o.id,
    o.name,
    COUNT(d.id) AS domains_count
FROM organizations AS o
JOIN domains AS d
    ON d.organization_id = o.id
GROUP BY o.id, o.name
HAVING COUNT(d.id) >= :min_domains
ORDER BY domains_count DESC, o.name;
