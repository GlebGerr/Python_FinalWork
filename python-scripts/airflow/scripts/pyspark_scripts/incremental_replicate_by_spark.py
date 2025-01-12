import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def initialize_spark_session(app_name, jars):
    """
    Инициализирует SparkSession с заданным именем приложения и jar-файлами.

    Args:
        app_name (str): Имя приложения.
        jars (str): Путь к jar-файлам.

    Returns:
        SparkSession: Объект SparkSession.
    """
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.jars", jars) \
        .getOrCreate()

def read_audit_log(spark, source_url, source_driver):
    """
    Считывает необработанные изменения из audit_log.

    Args:
        spark (SparkSession): SparkSession.
        source_url (str): JDBC URL источника данных.
        source_driver (str): JDBC драйвер источника данных.

    Returns:
        DataFrame: Данные из audit_log.
    """
    query = """
        SELECT change_id, table_name, operation, old_data, new_data
        FROM audit_log
        WHERE is_processed = FALSE
        ORDER BY change_id
    """
    return spark.read.format("jdbc") \
        .option("url", source_url) \
        .option("driver", source_driver) \
        .option("query", query) \
        .load()

def process_changes(spark, changes_df, target_url, target_driver):
    """
    Обрабатывает изменения, сгруппированные по таблицам и операциям.

    Args:
        spark (SparkSession): SparkSession.
        changes_df (DataFrame): Данные изменений.
        target_url (str): JDBC URL целевой базы данных.
        target_driver (str): JDBC драйвер целевой базы данных.
    """
    grouped = changes_df.groupBy("table_name", "operation").agg(
        F.collect_list(F.struct("old_data", "new_data")).alias("changes")
    )

    for row in grouped.collect():
        table, operation, changes = row['table_name'], row['operation'], row['changes']
        logger.info(f"Обработка {operation} для таблицы {table} ({len(changes)} изменений)")

        if operation == "INSERT":
            new_data = [c['new_data'] for c in changes]
            new_data_df = spark.read.json(spark.sparkContext.parallelize(new_data))

            existing_data_df = spark.read.format("jdbc") \
                .option("url", target_url) \
                .option("driver", target_driver) \
                .option("dbtable", table) \
                .load()

            filtered_new_data_df = new_data_df.join(existing_data_df, how="left_anti")

            filtered_new_data_df.write.format("jdbc") \
                .option("url", target_url) \
                .option("driver", target_driver) \
                .option("dbtable", table) \
                .mode("append") \
                .save()
        else:
            logger.warning(f"Операция {operation} для таблицы {table} не поддерживается.")

def update_audit_log_status(spark, source_url, source_driver, max_change_id):
    """
    Обновляет статус обработанных изменений в audit_log.

    Args:
        spark (SparkSession): SparkSession.
        source_url (str): JDBC URL источника данных.
        source_driver (str): JDBC драйвер источника данных.
        max_change_id (int): Максимальный ID изменения для обновления.
    """
    query = f"SELECT mark_changes_as_processed({max_change_id});"
    try:
        connection = spark._sc._gateway.jvm.java.sql.DriverManager.getConnection(source_url)
        cursor = connection.createStatement()
        cursor.execute(query)
        logger.info("Статус обновлений успешно обновлен.")
    except Exception as e:
        logger.error(f"Ошибка обновления статуса: {e}", exc_info=True)
        raise
    finally:
        connection.close()

def main():
    parser = argparse.ArgumentParser(description="Incremental Replication with Spark")
    parser.add_argument('--source_url', required=True, help="JDBC URL источника данных")
    parser.add_argument('--source_driver', required=True, help="JDBC драйвер источника данных")
    parser.add_argument('--target_url', required=True, help="JDBC URL целевой базы данных")
    parser.add_argument('--target_driver', required=True, help="JDBC драйвер целевой базы данных")
    parser.add_argument('--jars', required=True, help="Список jar-файлов для Spark")

    args = parser.parse_args()

    spark = initialize_spark_session("Incremental Replication", args.jars)

    try:
        changes_df = read_audit_log(spark, args.source_url, args.source_driver)

        if changes_df.isEmpty():
            logger.info("Нет изменений для обработки.")
            return

        process_changes(spark, changes_df, args.target_url, args.target_driver)

        max_change_id = changes_df.agg({"change_id": "max"}).collect()[0][0]
        update_audit_log_status(spark, args.source_url, args.source_driver, max_change_id)

    except Exception as e:
        logger.error(f"Ошибка выполнения: {e}", exc_info=True)
        raise

    finally:
        spark.stop()
        logger.info("Spark сессия завершена.")

if __name__ == "__main__":
    main()
