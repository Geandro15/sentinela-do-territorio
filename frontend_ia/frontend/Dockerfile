# Sentinela do Território, Global Solution CitizenTech
# GEANDRO (RM 562316) | LUCAS VERO (RM 564202) | ROBERTO EDUARDO (RM 564537)
#
# Build com o contexto em frontend_ia/ (veja frontend_ia/docker-compose.yml).
FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY frontend /app/frontend

ENV PYTHONPATH=/app
EXPOSE 7860

CMD ["python", "-m", "frontend.app"]
