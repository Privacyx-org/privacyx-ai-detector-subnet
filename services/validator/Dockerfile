FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /app/app/
EXPOSE 7070
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","7070"]
