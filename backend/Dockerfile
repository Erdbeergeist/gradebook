FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY entrypoint.sh .
COPY migrations ./migrations

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
