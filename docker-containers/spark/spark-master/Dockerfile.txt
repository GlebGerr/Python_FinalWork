FROM bitnami/spark:3.5.3

USER root
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    curl

RUN curl -o /opt/bitnami/spark/jars/postgresql-42.2.18.jar https://jdbc.postgresql.org/download/postgresql-42.2.18.jar && \
    curl -o /opt/bitnami/spark/jars/mysql-connector-java-8.3.0.jar https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.3.0/mysql-connector-j-8.3.0.jar

USER 1001:1001