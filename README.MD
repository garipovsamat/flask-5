1. Подготовка виртуалки
Требования:

Выполнять все с запущенным впн
Ubuntu 22.04/24.04
2 CPU, 4 GB RAM, 20 GB диска
Доступ по SSH (или напрямую)

2. Установить Ansible (если нет)
```bash
sudo apt update && sudo apt install ansible -y
```
3. Скачать репозиторий
```bash
git clone https://github.com/garipovsamat/flask-5.git
cd flask-5
```
4. Настроить inventory.ini
Если запуск на самой виртуалке:

```bash
echo "[all]" > ansible/inventory.ini
echo "localhost ansible_connection=local" >> ansible/inventory.ini
```
Если подключение по SSH (замени IP и пользователя):

```ini
[all]
192.168.1.100 ansible_user=username ansible_ssh_pass=your_password
```
5. Запустить деплой
```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml
```
Через 5-7 минут всё будет готово.

Проверка работы
Поды
```bash
kubectl get pods -n flask-app
```
API
```bash
# Получить порт
kubectl get svc flask-app -n flask-app

# Проверить health
curl localhost:3xxxx/health

# Создать товар
curl -X POST localhost:3xxxx/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Тест", "price": 999}'

# Получить список
curl localhost:3xxxx/items
```

ArgoCD
Доступ
```bash
kubectl get svc argocd-server -n argocd
```
# HTTPS порт вида 443:3xxxx/TCP
Открой в браузере:

```text
https://<IP_виртуалки>:3xxxx
Логин: admin
Пароль: выводится в конце выполнения плейбука (или можно получить командой ниже)
```

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```
Приложение в ArgoCD
После входа нужно создать приложение:

Repository: https://github.com/garipovsamat/flask-5.git

Path: flask-chart

Namespace: flask-app

Очистка
```bash
# Удалить namespace с приложением
kubectl delete namespace flask-app

# Удалить ArgoCD
kubectl delete namespace argocd

# Полная очистка k3s
sudo /usr/local/bin/k3s-uninstall.sh
```