-- WALL_E_DB_USER - wall_e
-- WALL_E_DB_PASSWORD - wallEPassword
-- WALL_E_DB_DBNAME - csss_discord_db

CREATE USER wall_e WITH PASSWORD 'wallEPassword';
CREATE DATABASE csss_discord_db;
GRANT CONNECT ON DATABASE csss_discord_db TO wall_e;
GRANT ALL PRIVILEGES ON DATABASE csss_discord_db TO wall_e;