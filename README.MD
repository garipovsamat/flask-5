Playbook: Развертывание CRUD приложения на Flask с кешированием
1. Запуск приложения

``` bash
# Запустить все сервисы
docker-compose up -d

# Проверить статус контейнеров
docker-compose ps 
```
Ожидаемый результат:

```text
     Name                    Command               State           Ports         
--------------------------------------------------------------------------------
flask_app        uwsgi --ini uwsgi.ini             Up      5000/tcp              
nginx_proxy      nginx -g daemon off;              Up      0.0.0.0:80->80/tcp    
postgres_db      docker-entrypoint.sh postgres     Up      0.0.0.0:5432->5432/tcp
redis_cache      docker-entrypoint.sh redis ...    Up      0.0.0.0:6379->6379/tcp 
```
2. Проверка работоспособности
```bash
Invoke-WebRequest -Uri http://localhost/health -UseBasicParsing
```
Ожидаемый ответ:

```json
{"status":"healthy"}
```
3. Работа с приложением
3.1 Создание записи (Create)
``` bash
Invoke-WebRequest -Uri http://localhost/items -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"name": "Ноутбук", "description": "Игровой ноутбук", "price": 999.99}' -UseBasicParsing
```
Ожидаемый ответ:

``` json
{
  "id": 1,
  "name": "Ноутбук",
  "description": "Игровой ноутбук",
  "price": 999.99,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
} 
```

3.2 Получение всех записей (Read)
```bash
# Первый запрос - данные из БД (кеш пропущен)
(Invoke-WebRequest -Uri http://localhost/items -UseBasicParsing).Headers

# Второй запрос - данные из кеша
(Invoke-WebRequest -Uri http://localhost/items -UseBasicParsing).Headers
```
3.3 Получение одной записи
``` bash
Invoke-WebRequest -Uri http://localhost/items/1 -UseBasicParsing | Select-Object -ExpandProperty Content
```
Ожидаемый ответ:

``` json
{
  "id": 1,
  "name": "Ноутбук",
  "description": "Игровой ноутбук",
  "price": 999.99,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
} 
```
3.4 Обновление записи (Update)
``` bash
Invoke-WebRequest -Uri http://localhost/items/1 -Method PUT -Headers @{"Content-Type"="application/json"} -Body '{"price": 899.99}' -UseBasicParsing
```
3.5 Удаление записи (Delete)
``` bash
Invoke-WebRequest -Uri http://localhost/items/1 -Method DELETE -UseBasicParsing
```
Ожидаемый ответ:

``` json
{"message":"Item deleted successfully"} 
```
4. Проверка кеширования
4.1 Проверка Redis кеша
``` bash
# Подключиться к Redis
docker exec -it redis_cache redis-cli

# Посмотреть ключи
KEYS *

# Посмотреть значение кеша
GET items

# Проверить время жизни кеша
TTL items

# Выйти
exit
```
4.2 Проверка Nginx кеша
``` bash
# Проверить заголовки кеширования
(Invoke-WebRequest -Uri http://localhost/items -UseBasicParsing).Headers
```
Ожидаемые заголовки:

``` text
HTTP/1.1 200 OK
X-Cache-Status: HIT
Cache-Control: max-age=300 
```
4.3 Проверка инвалидации кеша
``` bash
# Создать запись (сбрасывает кеш)
Invoke-WebRequest -Uri http://localhost/items -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"name": "Мышь", "price": 29.99}' -UseBasicParsing

# Проверить что кеш сбросился
(Invoke-WebRequest -Uri http://localhost/items -UseBasicParsing).Headers
# Должно быть: X-Cache-Status: MISS
```
5. Управление приложением
5.1 Просмотр логов
``` bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f app
docker-compose logs -f nginx
docker-compose logs -f db
docker-compose logs -f redis 
```
5.2 Остановка приложения
``` bash
# Остановить все сервисы
docker-compose down

# Остановить и удалить volumes (очистить данные)
docker-compose down -v 
```
