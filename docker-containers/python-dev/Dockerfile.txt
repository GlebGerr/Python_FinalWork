# Используем базовый образ Python
FROM python:3.10-slim

# Устанавливаем необходимые утилиты и OpenJDK
RUN apt-get update && apt-get install -y \
    software-properties-common \
    build-essential \
    wget \
    curl \
    gnupg \
    git \
    vim \
    openjdk-17-jdk && \
    apt-get clean

# Устанавливаем переменные окружения для Java
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"
ENV SPARK_VERSION=3.5.3

# Устанавливаем pipenv и дополнительные пакеты
RUN pip install --upgrade pip pipenv

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости из requirements.txt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Переменные окружения Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Открываем порт для разработки
EXPOSE 8000 8888

CMD ["bash"]
