from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
from scripts.helpers.airflow_common import get_connection_uri

# Константы
SPARK_JARS = "/opt/airflow/spark/jars/postgresql-42.2.18.jar,/opt/airflow/spark/jars/mysql-connector-java-8.3.0.jar"
SCRIPT_PATH = '/opt/airflow/scripts/pyspark_scripts/incremental_replicate_by_spark.py'

# Параметры DAG
default_dag_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 10),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=3),
    "catchup": False,
    "concurrency": 1,
}

with DAG(
    dag_id="data_replication_audit_log",
    default_args=default_dag_args,
    description="Data replication with Spark using audit log",
    schedule_interval=timedelta(minutes=10),
    concurrency=4,
    max_active_runs=1,
) as dag:

    # Подготовка подключений
    postgres_conn = PostgresHook.get_connection("coursework_de_postgresql")
    mysql_conn = MySqlHook.get_connection("coursework_de_mysql")

    source_connection_url = get_connection_uri(postgres_conn)
    target_connection_url = get_connection_uri(mysql_conn)

    spark_config = {
        "spark.driver.memory": "1g",
        "spark.worker.memory": "1g",
        "spark.worker.cores": 1,
        "spark.executor.memory": "1g",
    }

    # Описание задач
    start_task = EmptyOperator(task_id="start_pipeline")
    end_task = EmptyOperator(task_id="end_pipeline")

    spark_task = SparkSubmitOperator(
        task_id="spark_data_replication",
        application=SCRIPT_PATH,
        conn_id="coursework_de_spark",
        application_args=[
            "--source_url", source_connection_url,
            "--source_driver", "org.postgresql.Driver",
            "--target_url", target_connection_url,
            "--target_driver", "com.mysql.cj.jdbc.Driver",
            "--jars", SPARK_JARS,
        ],
        conf=spark_config,
        jars=SPARK_JARS,
    )

    # Установка зависимостей
    start_task >> spark_task >> end_task