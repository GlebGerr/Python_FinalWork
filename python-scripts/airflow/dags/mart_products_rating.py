from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

from scripts.helpers.airflow_common import get_connection_uri

# Константы
MYSQL_CONNECTOR_JAR = "/opt/airflow/spark/jars/mysql-connector-java-8.3.0.jar"
PRODUCTS_RATING_SCRIPT = '/opt/airflow/scripts/pyspark_scripts/pyspark_mart_products_rating.py'

# Параметры DAG по умолчанию
default_dag_settings = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

with DAG(
    dag_id='generate_products_rating_mart',
    default_args=default_dag_settings,
    description='Generate a data mart for product ratings in MySQL using Spark',
    schedule_interval=timedelta(minutes=10),
    concurrency=1,
    max_active_runs=1
) as dag:
    # Настройка подключения
    mysql_connection_uri = get_connection_uri(MySqlHook.get_connection('coursework_de_mysql'))
    mysql_driver = 'com.mysql.cj.jdbc.Driver'

    # Определение задач DAG
    start_pipeline = EmptyOperator(task_id='start_pipeline')
    end_pipeline = EmptyOperator(task_id='end_pipeline')

    spark_task = SparkSubmitOperator(
        task_id='run_products_rating_script',
        application=PRODUCTS_RATING_SCRIPT,
        conn_id='coursework_de_spark',
        application_args=[
            '--src_tgt_url', mysql_connection_uri,
            '--src_tgt_driver', mysql_driver,
        ],
        conf={
            "spark.driver.memory": "1g",
            "spark.worker.memory": "1g",
            "spark.worker.cores": 1,
            "spark.executor.memory": "1g"
        },
        jars=MYSQL_CONNECTOR_JAR
    )

    # Установка последовательности выполнения задач
    start_pipeline >> spark_task >> end_pipeline
