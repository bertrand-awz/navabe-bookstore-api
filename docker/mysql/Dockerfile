FROM mysql:8.4

COPY --chown=mysql:mysql data/NVB.csv /var/lib/mysql-files/NVB.csv
COPY data/schema.sql /docker-entrypoint-initdb.d/01-schema.sql
COPY data/docker_seed.sql /docker-entrypoint-initdb.d/02-seed.sql

