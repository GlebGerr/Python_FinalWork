import argparse
from pyspark.sql import SparkSession
import pyspark.sql.functions as F


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


def process_product_rating(products_df, reviews_df, categories_df):
    """Обрабатывает данные продуктов, рейтингов и категорий."""
    # Создание витрины с расчетом рейтинга и общего количества отзывов
    product_rating_df = (
        products_df.join(reviews_df, "product_id")
        .groupBy("product_id", "name", "category_id")
        .agg(F.avg("rating").alias("average_rating"), F.count("review_id").alias("total_reviews"))
        .withColumn("average_rating", F.round("average_rating", 2))
        .withColumnRenamed("name", "product_name")
    )

    # Присоединение категорий
    products_with_categories_df = (
        product_rating_df
        .join(categories_df, "category_id")
        .withColumnRenamed("name", "category_name")
        .drop("parent_category_id")
        .select("product_id", "product_name", "category_name", "average_rating", "total_reviews")
        .orderBy(F.desc("average_rating"))  # Сортировка по рейтингу
    )

    return products_with_categories_df


def write_data_to_db(df, url: str, driver: str, table: str):
    """Записывает DataFrame в базу данных, перезаписывая данные в целевой таблице."""
    df.write.format("jdbc") \
        .option("url", url) \
        .option("driver", driver) \
        .option("dbtable", table) \
        .mode("overwrite") \
        .save()


def create_products_rating_view(src_tgt_url: str, src_tgt_driver: str):
    """
    Создает или перезаписывает витрину рейтинга продуктов по категориям.

    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
    """
    # Инициализация Spark сессии
    spark = get_spark_session("Create_mart_products_rating_view")

    # Чтение данных
    products_df = read_data_from_db(spark, src_tgt_url, src_tgt_driver, "products")
    reviews_df = read_data_from_db(spark, src_tgt_url, src_tgt_driver, "reviews")
    categories_df = read_data_from_db(spark, src_tgt_url, src_tgt_driver, "productcategories")

    # Обработка данных
    product_rating_df = process_product_rating(products_df, reviews_df, categories_df)

    # Запись результата в целевую таблицу
    write_data_to_db(product_rating_df, src_tgt_url, src_tgt_driver, "mart_products_rating")

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

    create_products_rating_view(args.src_tgt_url, args.src_tgt_driver)


if __name__ == "__main__":
    main()