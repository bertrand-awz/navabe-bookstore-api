#!/bin/sh
set -eu

echo "Applying Navabe database migrations and default data..."

mysql_command() {
  MYSQL_PWD="${MYSQL_PASSWORD}" mysql \
    --batch \
    --skip-column-names \
    --host="${MYSQL_HOST}" \
    --port="${MYSQL_PORT}" \
    --user="${MYSQL_USER}" \
    "${MYSQL_DATABASE}" \
    "$@"
}

mysql_command --execute="
  CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(100) NOT NULL PRIMARY KEY,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
  );
"

already_applied=$(mysql_command --execute="
  SELECT COUNT(*) FROM schema_migrations WHERE version = '002_secure_credentials_and_payments';
")

if [ "${already_applied}" = "1" ]; then
  echo "Navabe database migration v2 is already applied."
else
  MYSQL_PWD="${MYSQL_PASSWORD}" mysql \
    --host="${MYSQL_HOST}" \
    --port="${MYSQL_PORT}" \
    --user="${MYSQL_USER}" \
    "${MYSQL_DATABASE}" \
    < /migrations/migration_v2.sql

  mysql_command --execute="
    INSERT INTO schema_migrations (version) VALUES ('002_secure_credentials_and_payments');
  "

  echo "Navabe database migration v2 applied."
fi

echo "Ensuring manager temporary password flag exists..."

mysql_command --execute="
  SET @column_exists := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'Administrateur'
      AND COLUMN_NAME = 'mot_de_passe_temporaire'
  );
  SET @migration_sql := IF(
    @column_exists = 0,
    'ALTER TABLE Administrateur ADD COLUMN mot_de_passe_temporaire BOOLEAN NOT NULL DEFAULT FALSE',
    'SELECT 1'
  );
  PREPARE migration_stmt FROM @migration_sql;
  EXECUTE migration_stmt;
  DEALLOCATE PREPARE migration_stmt;
"

echo "Ensuring default RootManager account exists..."

MYSQL_PWD="${MYSQL_PASSWORD}" mysql \
  --host="${MYSQL_HOST}" \
  --port="${MYSQL_PORT}" \
  --user="${MYSQL_USER}" \
  "${MYSQL_DATABASE}" <<'SQL'
INSERT INTO Administrateur(adminID, nom, prenom, mail, mot_de_passe, mot_de_passe_temporaire)
VALUES (
  'RTMGM1',
  'RootManager',
  'RootManager',
  'root.manager@test.navabe.bertawz.dev',
  'scrypt:32768:8:1$hC4Hl70ZeamtPNAU$33861e3b8c1973f5a946bb1527c104eb9004ccfe06a25cd584d7a693248733514fbb7b36b653bd24926cf4599fc266ac7c93cc3ead3e5e6ba54c871d78556d6c',
  TRUE
)
ON DUPLICATE KEY UPDATE
  adminID = 'RTMGM1',
  nom = 'RootManager',
  prenom = 'RootManager',
  mail = 'root.manager@test.navabe.bertawz.dev',
  mot_de_passe = 'scrypt:32768:8:1$hC4Hl70ZeamtPNAU$33861e3b8c1973f5a946bb1527c104eb9004ccfe06a25cd584d7a693248733514fbb7b36b653bd24926cf4599fc266ac7c93cc3ead3e5e6ba54c871d78556d6c',
  mot_de_passe_temporaire = TRUE;
SQL

echo "Default RootManager account is ready."
