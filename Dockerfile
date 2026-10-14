# Dockerfile · contenedor de la interfaz web (Gradio) para Google Cloud Run
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Dependencias (capa separada: se reutiliza si solo cambia el código)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Código y datos de solo lectura. Nada de .env, bases .db ni pruebas (ver .dockerignore)
COPY *.py ./
COPY data/*.csv data/
COPY data/politicas/ data/politicas/

# Cloud Run indica el puerto en la variable PORT (por defecto 8080)
CMD ["python", "app.py"]
