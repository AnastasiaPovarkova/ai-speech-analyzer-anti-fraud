# Используем официальный базовый образ Python (Slim версия)
FROM python:3.11-slim

# Указываем переменные окружения для предотвращения интерактивных запросов apt
ENV DEBIAN_FRONTEND=noninteractive

# Устанавливаем системные зависимости для сборки whisper.cpp и работы с аудио
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    ffmpeg \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию в контейнере
WORKDIR /app

# Скачиваем и компилируем whisper.cpp через cmake
RUN git clone https://github.com/ggerganov/whisper.cpp.git /opt/whisper.cpp && \
    cd /opt/whisper.cpp && \
    cmake -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build --config Release --target whisper-cli

# Добавляем whisper-cli в PATH
#ENV PATH="/opt/whisper.cpp:${PATH}"
ENV PATH="/opt/whisper.cpp/build/bin:${PATH}"

# Сначала копируем только файл зависимостей
COPY requirements.txt .

# Настройка pip для повышенной стабильности в контейнерах:
# --no-cache-dir уменьшает использование диска
# --default-timeout=100 предотвращает обрывы соединения на медленных дисках Mac
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Создаем папки для моделей и аудиозаписей
RUN mkdir -p models data/samples

# Скачиваем модель Whisper (base) прямо во время сборки образа
RUN curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin -o models/ggml-base.bin

# Копируем исходный код проекта
COPY src/ ./src/
COPY app.py .

# Указываем порты, которые использует Streamlit
EXPOSE 8501

# Настройки окружения Streamlit для корректной работы в контейнере
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Команда для запуска приложения
CMD ["streamlit", "run", "app.py"]