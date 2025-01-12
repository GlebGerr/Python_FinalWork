from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

from scripts.helpers.airflow_common import get_connection_uri

# Константы
MYSQL_DRIVER_JAR = "/opt/airflow/spark/jars/mysql-connector-java-8.3.0.jar"
PYSPARK_AVERAGE_CHECK_SCRIPT = '/opt/airflow/scripts/pyspark_scripts/pyspark_mart_average_check.py'

# Параметры по умолчанию для DAG
default_dag_parameters = {
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
    dag_id='generate_average_check_mart',
    default_args=default_dag_parameters,
    description='Generate a data mart of average checks in MySQL using Spark',
    schedule_interval=timedelta(minutes=10),
    concurrency=1,
    max_active_runs=1
) as dag:
    # Настройка подключения и параметры драйвера
    mysql_connection_uri = get_connection_uri(MySqlHook.get_connection('coursework_de_mysql'))
    mysql_driver_class = 'com.mysql.cj.jdbc.Driver'

    # Операторы DAG
    start_pipeline = EmptyOperator(task_id='pipeline_start')
    end_pipeline = EmptyOperator(task_id='pipeline_end')

    spark_job = SparkSubmitOperator(
        task_id='run_average_check_mart_script',
        application=PYSPARK_AVERAGE_CHECK_SCRIPT,
        conn_id='coursework_de_spark',
        application_args=[
            '--src_tgt_url', mysql_connection_uri,
            '--src_tgt_driver', mysql_driver_class,
        ],
        conf={
            "spark.driver.memory": "1g",
            "spark.worker.memory": "1g",
            "spark.worker.cores": 1,
            "spark.executor.memory": "1g"
        },
        jars=MYSQL_DRIVER_JAR
    )

    start_pipeline >> spark_job >> end_pipeline
