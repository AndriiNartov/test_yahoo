CREATE USER yahoo_user WITH PASSWORD 'devpass';

CREATE DATABASE yahoo_db;

GRANT ALL PRIVILEGES ON DATABASE yahoo_db TO yahoo_user;
