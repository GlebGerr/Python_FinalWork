CREATE USER airflow WITH PASSWORD 'airflow' CREATEDB;
CREATE DATABASE airflow_db
    WITH
    OWNER = airflow
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;