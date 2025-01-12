#!/bin/bash

# Запуск Airflow
airflow db migrate

# Создание юзеров
airflow users create \
    --username "$_AIRFLOW_WWW_USER_USERNAME" \
    --password "$_AIRFLOW_WWW_USER_PASSWORD" \
    --firstname Admin \
    --lastname Adminov \
    --role Admin \
    --email admin@administration.info

# Создание коннектов
airflow connections add 'coursework_de_postgresql' \
    --conn-json '{
        "conn_type": "postgres",
        "login": "'"$POSTGRESQL_APP_USER"'",
        "password": "'"$POSTGRESQL_APP_PASSWORD"'",
        "host": "'"$POSTGRESQL_APP_HOST"'",
        "port": 5432,
        "schema": "'"$POSTGRESQL_APP_DB"'",
        "extra": {
            "currentSchema": "'"$POSTGRESQL_APP_SCHEMA"'"
        }
    }'

airflow connections add 'coursework_de_mysql' \
    --conn-json '{
        "conn_type": "mysql",
        "login": "'"$MYSQL_APP_USER"'",
        "password": "'"$MYSQL_APP_PASSWORD"'",
        "host": "'"$MYSQL_APP_HOST"'",
        "port": 3306,
        "schema": "'"$MYSQL_APP_DB"'"
    }'

airflow connections add 'coursework_de_spark' \
    --conn-json '{
        "conn_type": "generic",
        "host": "spark://'"$SPARK_MASTER_HOST"'",
        "port": "'"$SPARK_MASTER_PORT"'",
        "extra": {
            "deploy-mode": "client",
            "spark_binary": "spark-submit"
        }
    }'

airflow version