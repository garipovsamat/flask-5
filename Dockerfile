FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    nginx \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/uwsgi_params /etc/nginx/uwsgi_params

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

CMD ["/start.sh"]