-- WALL_E_DB_USER - wall_e
-- WALL_E_DB_PASSWORD - postgres_passwd
-- WALL_E_DB_DBNAME - wall_e_db

CREATE USER wall_e WITH PASSWORD 'wall_e_postgres_passwd';
CREATE DATABASE wall_e_db;
GRANT CONNECT ON DATABASE wall_e_db TO wall_e;
GRANT ALL PRIVILEGES ON DATABASE wall_e_db TO wall_e;