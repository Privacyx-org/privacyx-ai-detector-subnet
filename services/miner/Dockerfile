FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /app/app/
# modèle copié après (on le montera par build context)
COPY models/ /app/models/
EXPOSE 6060
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","6060"]
