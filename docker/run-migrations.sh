#!/bin/sh
set -eu

echo "Applying Navabe database migration v2..."

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
  exit 0
fi

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
