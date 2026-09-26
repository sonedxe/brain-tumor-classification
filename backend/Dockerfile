FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

COPY backend/requirements.txt /code/backend/requirements.txt
RUN pip install --no-cache-dir -r /code/backend/requirements.txt

COPY backend /code/backend
COPY ml/configs /code/ml/configs
COPY .env.example /code/.env.example

WORKDIR /code/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
