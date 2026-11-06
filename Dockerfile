FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --create-home torneo
USER torneo
EXPOSE 8000
CMD ["gunicorn", "--reload", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app.web:app"]