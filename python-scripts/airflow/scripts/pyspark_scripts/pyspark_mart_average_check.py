import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def get_spark_session(app_name: str) -> SparkSession:
    """Создает и возвращает Spark сессию."""
    return SparkSession.builder.appName(app_name).getOrCreate()


def read_data_from_db(spark: SparkSession, url: str, driver: str, table: str):
    """Читает данные из базы данных по указанным параметрам."""
    return (
        spark.read
        .format("jdbc")
        .option("url", url)
        .option("driver", driver)
        .option("dbtable", table)
        .load()
    )


def process_data(orders_df, users_df):
    """Обрабатывает данные: объединяет таблицы и рассчитывает средний чек по статусам."""
    return (
        orders_df.join(users_df, "user_id")
        .groupBy("status", "loyalty_status")
        .agg(F.avg("total_amount").alias("average_check"))
        .withColumn("order_status", F.col("status"))
        .withColumn("average_check", F.round("average_check", 2))
        .drop("status")
    )


def write_data_to_db(df, url: str, driver: str, table: str):
    """Записывает DataFrame в базу данных, перезаписывая данные в целевой таблице."""
    df.write.format("jdbc") \
        .option("url", url) \
        .option("driver", driver) \
        .option("dbtable", table) \
        .mode("overwrite") \
        .save()


def create_average_check_view(src_tgt_url: str, src_tgt_driver: str):
    """
    Создает или перезаписывает витрину среднего чека с разбивкой по статусу заказа и лояльности.

    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
    """
    # Инициализация Spark сессии
    spark = get_spark_session("Create_mart_average_check")

    # Чтение данных
    orders_df = read_data_from_db(spark, src_tgt_url, src_tgt_driver, "orders")
    users_df = read_data_from_db(spark, src_tgt_url, src_tgt_driver, "users")

    # Обработка данных
    average_check_df = process_data(orders_df, users_df)

    # Запись результата в целевую таблицу
    write_data_to_db(average_check_df, src_tgt_url, src_tgt_driver, "mart_average_check")

    # Завершение работы с Spark
    spark.stop()


def parse_arguments() -> argparse.Namespace:
    """Парсит командные аргументы."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--src_tgt_url', type=str, required=True)
    parser.add_argument('--src_tgt_driver', type=str, required=True)
    return parser.parse_args()


def main():
    """Основная точка входа. Парсит аргументы и вызывает создание/перезапись витрины."""
    args = parse_arguments()

    create_average_check_view(args.src_tgt_url, args.src_tgt_driver)


if __name__ == "__main__":
    main()
