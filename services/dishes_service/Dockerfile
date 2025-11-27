FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=5002
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 5002
CMD ["/bin/sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT} app:app"]
