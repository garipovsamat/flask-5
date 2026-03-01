#!/bin/bash
# Запуск uwsgi в фоне
uwsgi --ini /app/uwsgi.ini &

# Запуск nginx на переднем плане
nginx -g "daemon off;"