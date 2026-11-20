# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)
#
# Este Dockerfile é construído com o contexto na RAIZ do projeto, porque o
# back-end importa o código de IA do PLN/Generative AI (genai/, assistente/,
# config.py, direto na raiz do projeto, sem uma pasta pln/ própria) e da
# Visão Computacional (visao/). Veja frontend_ia/docker-compose.yml.
FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema: libgomp1 (Pillow/tensorflow), ffmpeg (faster-whisper
# precisa para abrir áudio em formatos comprimidos como .mp3/.webm/.m4a)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/pln_requirements.txt
COPY visao/requirements.txt /app/visao_requirements.txt
COPY frontend_ia/backend/requirements.txt /app/backend_requirements.txt

RUN pip install --no-cache-dir -r /app/pln_requirements.txt \
    && pip install --no-cache-dir -r /app/visao_requirements.txt \
    && pip install --no-cache-dir -r /app/backend_requirements.txt

# Código do PLN/Generative AI, direto na raiz do projeto
COPY app.py config.py /app/
COPY genai /app/genai
COPY assistente /app/assistente
COPY corpus /app/corpus
COPY visao /app/visao
COPY frontend_ia/backend /app/frontend_ia/backend

WORKDIR /app/frontend_ia
ENV PYTHONPATH=/app/frontend_ia
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
