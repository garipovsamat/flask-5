1. Подготовка виртуалки
Требования:

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
Если на самой виртуалке:

```bash
echo "[all]" > ansible/inventory.ini
echo "localhost ansible_connection=local" >> ansible/inventory.ini
```
Если по SSH:

```ini
[all]
твой_ip_адрес ansible_user=root
(или ansible_user=ubuntu, если пользователь ubuntu)
```

5. Запустить одной командой
```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml
```
6. Проверить что всё работает
```bash
# Поды должны быть все в статусе Running
kubectl get pods -n flask-app

# Проверить API
curl localhost:32185/health
curl localhost:32185/items

# Создать тестовый товар
curl -X POST localhost:32185/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Тест", "price": 999}'

# Получить список
curl localhost:32185/items
```
7. ArgoCD 
```bash
# Проброс порта (в отдельном терминале)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Логин: admin
# Пароль:
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```
8. Если что-то не так
```bash
# Посмотреть логи
kubectl logs -n flask-app -l app=flask-app

# Перезапустить поды
kubectl delete pods -n flask-app --all

# Полностью очистить
helm uninstall flask-app -n flask-app
kubectl delete namespace flask-app
```